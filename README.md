# ios-app
This is the code for an iOS app, which has functin of register, login and other activities on the backend. The app also contains function of scanning QR code and generating QR code.

# Useage
The deployment is very straightforward.

First we need to install Xcode on the mac. Xcode can be installed directly on App store.

After successfully install Xcode, just need to click and run the file appDemoOne.xcworkspace

If you need to deploy the app on the iphone, there is the guidance https://codewithchris.com/deploy-your-app-on-an-iphone/

The main structure of the code is in the folder appDemoOne

The login function is achieved by the files LoginViewController.h and LoginViewController.m, while the register function is achieved by RegistViewController.h and RegistViewController.m. The layout of the app is decided by MainViewController.m and MenuView.m. Also we can directly change the .xib files to change the views of the app. Changing of .xib files is not by coding, instead we just draw the view.

The code that run on the backend is serverFlask_pi_remote_4_him_rsa.py, which is mainly contributed by Jingping Nie

If you want to deploy the app on your phone you can follow the instructions below:

First connect your phone to the computer and trust the device, then choose the simulator as your device.

Second click appDemoOne, then click signing & capabilities. You should choose your own team

Finally click run to start the process
