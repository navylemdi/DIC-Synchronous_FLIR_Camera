#https://github.com/SocCog-Team/Multiple-Cameras-Acquisition/blob/master/SpinnakerCamera.py
import os
import PySpin
import sys
import time
import matplotlib.pyplot as plt

NUM_IMAGES = 5  # number of images to grab
GAIN = 38 #Gain of the cameras
EXPOSURE_TIME = 10000 #Exposure time of the cameras in ms  MIN = 6.258488 MAX = 13181.507587432861
FILEPATH = ['/Users/yvan/Test/Tiff2cam/Cam1', '/Users/yvan/Test/Tiff2cam/Cam2']
FORMAT = '.tif'

def acquire_images(cam_list):
    """
    This function acquires and saves 10 images from each device.

    :param cam_list: List of cameras
    :type cam_list: CameraList
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    print('*** IMAGE ACQUISITION ***\n')
    try:
        result = True

        # Prepare each camera to acquire images
        #
        # *** NOTES ***
        # For pseudo-simultaneous streaming, each camera is prepared as if it
        # were just one, but in a loop. Notice that cameras are selected with
        # an index. We demonstrate pseduo-simultaneous streaming because true
        # simultaneous streaming would require multiple process or threads,
        # which is too complex for an example.
        #

        for i, cam in enumerate(cam_list):

            # Set acquisition mode to continuous
            node_acquisition_mode = PySpin.CEnumerationPtr(cam.GetNodeMap().GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (node retrieval; camera %d). Aborting... \n' % i)
                return False

            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval %d). \
                Aborting... \n' % i)
                return False

            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            print('Camera %d acquisition mode set to continuous...' % i)

            # Begin acquiring images
            
            cam.BeginAcquisition()

            print('Camera %d started acquiring images...' % i)

            print()

        # Retrieve, convert, and save images for each camera
        #
        # *** NOTES ***
        # In order to work with simultaneous camera streams, nested loops are
        # needed. It is important that the inner loop be the one iterating
        # through the cameras; otherwise, all images will be grabbed from a
        # single camera before grabbing any images from another.
        for n in range(NUM_IMAGES):
            time.sleep(0.05) #Permet d'empecher de prendre une photo trop vite ou trop tard
            #Si pas mis : 2 images peuvent etre prise par 1 camera en mm temps car le dirac emis par l'arduino possede une largeur.
            #Si time.sleep(1) : Une image peut sauter une seconde car le sleep n'est pas exactement egal à 1s. On rate le dirac de l'arduino et on prends le prochain qui arrive 1s plus tard
            for i, cam in enumerate(cam_list):
                try:
                    # Retrieve device serial number for filename
                    node_device_serial_number = PySpin.CStringPtr(cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

                    if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                        device_serial_number = node_device_serial_number.GetValue()
                        print('Camera %d serial number set to %s...' % (i, device_serial_number))

                    # Retrieve next received image and ensure image completion
                    image_result = cam.GetNextImage()

                    if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ... \n' % image_result.GetImageStatus())
                    else:
                        # Print image information
                        width = image_result.GetWidth()
                        height = image_result.GetHeight()
                        print('Camera %d grabbed image %d, width = %d, height = %d' % (i, n, width, height))

                        # Convert image to mono 8
                        image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)

                        # Create a unique filename type: PATH/XXXX_Y.FORMAT
                        filename = FILEPATH[i] + '/' + str(n).zfill(4)+ '_' + str(i) + FORMAT #AcquisitionMultipleCamera-%s-%d.tiff' % (device_serial_number, n)
                        # Getting the image data as a numpy array
                        image_data = image_result.GetNDArray()

                        print('Camera ',i, ' gain set at ' , cam.Gain.GetValue())
                        print('Camera ',i, ' exposure time set at ' , cam.ExposureTime.GetValue())
                        
                        # Draws an image on the current figure
                        plt.imshow(image_data, cmap='gray')

                        # Interval in plt.pause(interval) determines how fast the images are displayed in a GUI
                        # Interval is in seconds.
                        plt.pause(0.001)

                        # Clear current reference of a figure. This will improve display speed significantly
                        plt.clf()
                        # Save image
                        image_converted.Save(filename)
                        print('Image saved at %s' % filename)

                    # Release image
                    image_result.Release()
                    print()

                except PySpin.SpinnakerException as ex:
                    print('Error: %s' % ex)
                    result = False

        # End acquisition for each camera
        #
        # *** NOTES ***
        # Notice that what is usually a one-step process is now two steps
        # because of the additional step of selecting the camera. It is worth
        # repeating that camera selection needs to be done once per loop.
        #
        # It is possible to interact with cameras through the camera list with
        # GetByIndex(); this is an alternative to retrieving cameras as
        # CameraPtr objects that can be quick and easy for small tasks.
        for cam in cam_list:

            # End acquisition
            cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result

def print_device_info(nodemap, cam_num):
    """
    This function prints the device information of the camera from the transport
    layer; please see NodeMapInfo example for more in-depth comments on printing
    device information from the nodemap.

    :param nodemap: Transport layer device nodemap.
    :param cam_num: Camera number.
    :type nodemap: INodeMap
    :type cam_num: int
    :returns: True if successful, False otherwise.
    :rtype: bool
    """

    print('Printing device information for camera %d... \n' % cam_num)

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print('%s: %s' % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

        else:
            print('Device control information not available.')
        print()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result

def run_multiple_cameras(cam_list, gain, exposure_time):
    """
    This function acts as the body of the example; please see NodeMapInfo example
    for more in-depth comments on setting up cameras.

    :param cam_list: List of cameras
    :type cam_list: CameraList
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Retrieve transport layer nodemaps and print device information for
        # each camera
        # *** NOTES ***
        # This example retrieves information from the transport layer nodemap
        # twice: once to print device information and once to grab the device
        # serial number. Rather than caching the nodem#ap, each nodemap is
        # retrieved both times as needed.
        print('*** DEVICE INFORMATION ***\n')

        for i, cam in enumerate(cam_list):

            # Retrieve TL device nodemap
            nodemap_tldevice = cam.GetTLDeviceNodeMap()

            # Print device information
            result &= print_device_info(nodemap_tldevice, i)

        # Initialize each camera
        #
        # *** NOTES ***
        # You may notice that the steps in this function have more loops with
        # less steps per loop; this contrasts the AcquireImages() function
        # which has less loops but more steps per loop. This is done for
        # demonstrative purposes as both work equally well.
        #
        # *** LATER ***
        # Each camera needs to be deinitialized once all images have been
        # acquired.

        for i, cam in enumerate(cam_list):

            # Initialize camera
            cam.Init()


            cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            cam.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
            cam.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
            cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

            cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            cam.Gain.SetValue(gain)
            cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            cam.ExposureTime.SetValue(min(cam.ExposureTime.GetMax(), exposure_time))
            print('Camera ',i, ' gain set at ' , cam.Gain.GetValue())
            print('Camera ',i, ' exposure time set at ' , cam.ExposureTime.GetValue())

        # Acquire images on all cameras
        result &= acquire_images(cam_list)
        # Deinitialize each camera
        #
        # *** NOTES ***
        # Again, each camera must be deinitialized separately by first
        # selecting the camera and then deinitializing it.
        for cam in cam_list:

            # Deinitialize camera
            cam.DeInit()

        # Release reference to camera
        # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
        # cleaned up when going out of scope.
        # The usage of del is preferred to assigning the variable to None.
        del cam

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result

def create_folders():
    for Path in FILEPATH:
        if not os.path.exists(Path):
            print()
            input('Press enter to create folder ' + Path)
            os.makedirs(Path)
           
def main():
    """
    Example entry point; please see Enumeration example for more in-depth
    comments on preparing and cleaning up the system.

    :return: True if successful, False otherwise.
    :rtype: bool
    """

    # Since this application saves images in the current folder
    # we must ensure that we have permission to write to this folder.
    # If we do not have permission, fail right away.
    
    

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    #Create folders that doesn't exist yet
    create_folders()

    # Get current library version
    version = system.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))
    result =True
    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()
    
    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)
    
    # Finish if there are no cameras
    if num_cameras == 0:

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')
        return False
    
    # Run example on all cameras
    print('Running example for all cameras...')

    result = run_multiple_cameras(cam_list, GAIN, EXPOSURE_TIME)

    print('Example complete... \n')

    # Clear camera list before releasing system
    cam_list.Clear()
    
    # Release system instance
    system.ReleaseInstance()

    input('Done! Press Enter to exit...')
    return result

if __name__ == '__main__':
    if main():
        sys.exit(0)
    else:
        sys.exit(1)