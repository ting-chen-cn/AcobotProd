'''OpenCV Camera Class
		Camera is a class use openCV to get access to a webCamera.
		video_source is the variable used to manage the cameras when there is multiple cameras connect to the computer, the default value is0.
		crop_coordinate_scaled is a variable to control the output size of the camera, it's defined by two crop points (Upper left point, lower right) scaled coordinates [0,1].
		get_frame() function return the status of the operation and the cropped image.
		imageSize() function return the width and height of the get_frame returned image.
'''
import cv2

class Camera:
	def __init__(self,video_source=0,crop_coordinate_scaled={'left':0,'right':1,'top':0,'bottom':1}):
		self.video_source = video_source
		self.camera = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
		self.crop_coordinate_scaled = crop_coordinate_scaled
		self.crop_width = self.camera.get(3)
		self.crop_height = self.camera.get(4)


	def stop(self):
		self.camera.release()

	def getImage(self):	
		success, img = self.camera.read()
		if not success:
			print("Can't receive frame (stream end?). Exiting ...")
			return []
		else:
			width = img.shape[1]
			height = img.shape[0]
			L=int(self.crop_coordinate_scaled['left']*width)
			T=int(self.crop_coordinate_scaled['top']*height)
			R=int(self.crop_coordinate_scaled['right']*width)
			B=int(self.crop_coordinate_scaled['bottom']*height)
			crop_img = img[T:B,L:R]
			self.crop_width = crop_img.shape[1]
			self.crop_height = crop_img.shape[0]
			# We are using Motion JPEG, but OpenCV defaults to capture raw images,
      # so we must encode it into JPEG in order to correctly display the
      # video stream.
			
			return  crop_img

	def imageSize(self):
		return self.crop_width, self.crop_height