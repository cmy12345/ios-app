//
//  LoginViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/11/12.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "LoginViewController.h"
#import "MainViewController.h"
#import "RegistViewController.h"
#import "AboutViewController.h"
#import <AVFoundation/AVFoundation.h>
@interface LoginViewController ()
@property (weak, nonatomic) IBOutlet UITextField *phoneTextField;
@property (weak, nonatomic) IBOutlet UITextField *passwordTextField;
@property (weak, nonatomic) IBOutlet UITextField *deviceIdTextField;


@end

@implementation LoginViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"Login";
    NSString *username = UDValue(@"myphone") ? UDValue(@"myphone") : @"";
    NSString *mypassword = UDValue(@"mypassword") ? UDValue(@"mypassword") : @"";
    NSString *mydeviceId = UDValue(@"mydeviceId") ? UDValue(@"mydeviceId") : @"";
    if (![username isEqualToString:@""]) {
        self.phoneTextField.text =username;
    }
    if (![mypassword isEqualToString:@""]) {
        self.passwordTextField.text =mypassword;
    }
    if (![mydeviceId isEqualToString:@""]) {
        self.deviceIdTextField.text =mydeviceId;
    }
}
- (IBAction)loginBtnCkick:(id)sender {
    if ([self isBlankString:_phoneTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入用户名"];
        return;
    }
    if ([self isBlankString:_passwordTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入密码"];
        return;
    }
    if ([self isBlankString:_deviceIdTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入deviceId"];
        return;
    }
    
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:_deviceIdTextField.text forKey:@"deviceID"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] newPOST:postPemByDeviceId parameters:requestDic success:^(id responseObject) {
        SETUDValue(responseObject, @"RsaPublicKey");
        SETUDValue(self->_deviceIdTextField.text, @"LocaldeviceID");
        UDSYNC;
        [self login];
        
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
    
    
    
   
    
}

- (void)login{
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:_phoneTextField.text forKey:@"Username"];
    [requestDic setValue:_passwordTextField.text forKey:@"Password"];
    [requestDic setValue:_deviceIdTextField.text forKey:@"deviceID"];
    [[DXNetworkCenter managerDXNetwork] POST:PostLogin parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        if ([responseObject isEqualToString:@"1"] || [responseObject isEqualToString:@"2"]) {

            SETUDValue(self->_phoneTextField.text, @"myphone");
            SETUDValue(self->_passwordTextField.text, @"mypassword");
            SETUDValue(self->_deviceIdTextField.text, @"mydeviceId");
            UDSYNC;
            for (UIView *v in [UIApplication sharedApplication].keyWindow.subviews) {
                [v removeFromSuperview];
            }
            MainViewController *mainVC = [[MainViewController alloc] init];
            UINavigationController *nav = [[UINavigationController alloc] initWithRootViewController:mainVC];
            [UIApplication sharedApplication].keyWindow.rootViewController = nav;
        }else{
            [SVProgressHUD showErrorWithStatus:@"Login Failed"];
        }

    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
}

- (IBAction)registBtnClick:(id)sender {
    RegistViewController *vc = [[RegistViewController alloc] init];
    [self.navigationController pushViewController:vc animated:YES];
}
- (IBAction)saomaBtnClick:(id)sender {
    __weak typeof(self) weakSelf = self;
    AboutViewController *aboutVC = [[AboutViewController alloc] init];
    aboutVC.isLogin = @"login";
    aboutVC.comfireBlock = ^(NSString *result) {
        weakSelf.deviceIdTextField.text = result;
    };
    [self QRCodeScanVC:aboutVC];
    
}

- (void)QRCodeScanVC:(UIViewController *)scanVC {
    AVCaptureDevice *device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo];
    if (device) {
        AVAuthorizationStatus status = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeVideo];
        switch (status) {
                case AVAuthorizationStatusNotDetermined: {
                    [AVCaptureDevice requestAccessForMediaType:AVMediaTypeVideo completionHandler:^(BOOL granted) {
                        if (granted) {
                            dispatch_sync(dispatch_get_main_queue(), ^{
                                [self.navigationController pushViewController:scanVC animated:YES];
                            });
                            NSLog(@"用户第一次同意了访问相机权限 - - %@", [NSThread currentThread]);
                        } else {
                            NSLog(@"用户第一次拒绝了访问相机权限 - - %@", [NSThread currentThread]);
                        }
                    }];
                    break;
                }
                case AVAuthorizationStatusAuthorized: {
                    [self.navigationController pushViewController:scanVC animated:YES];
                    break;
                }
                case AVAuthorizationStatusDenied: {
                    UIAlertController *alertC = [UIAlertController alertControllerWithTitle:@"温馨提示" message:@"请去-> [设置 - 隐私 - 相机 - SGQRCodeExample] 打开访问开关" preferredStyle:(UIAlertControllerStyleAlert)];
                    UIAlertAction *alertA = [UIAlertAction actionWithTitle:@"确定" style:(UIAlertActionStyleDefault) handler:^(UIAlertAction * _Nonnull action) {
                        
                    }];
                    
                    [alertC addAction:alertA];
                    [self presentViewController:alertC animated:YES completion:nil];
                    break;
                }
                case AVAuthorizationStatusRestricted: {
                    NSLog(@"因为系统原因, 无法访问相册");
                    break;
                }
                
            default:
                break;
        }
        return;
    }
    
    UIAlertController *alertC = [UIAlertController alertControllerWithTitle:@"温馨提示" message:@"未检测到您的摄像头" preferredStyle:(UIAlertControllerStyleAlert)];
    UIAlertAction *alertA = [UIAlertAction actionWithTitle:@"确定" style:(UIAlertActionStyleDefault) handler:^(UIAlertAction * _Nonnull action) {
        
    }];
    
    [alertC addAction:alertA];
    [self presentViewController:alertC animated:YES completion:nil];
}


- (BOOL) isBlankString:(NSString *)string {
    NSString *str = [NSString stringWithFormat:@"%@",string];
    if (str == nil || str == NULL) {
        return YES;
    }
    if ([str isKindOfClass:[NSNull class]]) {
        return YES;
    }
    if ([str isEqualToString:@"(null)"]) {
        return YES;
    }
    if ([str isEqualToString:@"<null>"]) {
        return YES;
    }
    if ([[str stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]] length]==0) {
        return YES;
    }
    return NO;
}

/*
#pragma mark - Navigation

// In a storyboard-based application, you will often want to do a little preparation before navigation
- (void)prepareForSegue:(UIStoryboardSegue *)segue sender:(id)sender {
    // Get the new view controller using [segue destinationViewController].
    // Pass the selected object to the new view controller.
}
*/

@end
