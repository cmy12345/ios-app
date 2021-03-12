//
//  RegistViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/11/14.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "RegistViewController.h"
#import "AboutViewController.h"
#import <AVFoundation/AVFoundation.h>

@interface RegistViewController ()
@property (weak, nonatomic) IBOutlet UITextField *firstNameTextField;
@property (weak, nonatomic) IBOutlet UITextField *lastNameTextField;
@property (weak, nonatomic) IBOutlet UITextField *userNameTextField;
@property (weak, nonatomic) IBOutlet UITextField *enailTextField;
@property (weak, nonatomic) IBOutlet UITextField *passwordTextField;
@property (weak, nonatomic) IBOutlet UITextField *repeatPasswordTextField;
@property (weak, nonatomic) IBOutlet UITextField *deviceIDTextField;
@end

@implementation RegistViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"Register";
}
- (IBAction)comfireBtnClick:(id)sender {
    if ([self isBlankString:_firstNameTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入firstName"];
        return;
    }
    if ([self isBlankString:_lastNameTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入lastName"];
        return;
    }
    if ([self isBlankString:_userNameTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入userName"];
        return;
    }
    if ([self isBlankString:_enailTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入email"];
        return;
    }
    if ([self isBlankString:_passwordTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入password"];
        return;
    }
    if ([self isBlankString:_repeatPasswordTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"repeatPassword"];
        return;
    }
    if (![_passwordTextField.text isEqualToString:_repeatPasswordTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"两次输入密码不同！"];
               return;
    }
    if ([self isBlankString:_deviceIDTextField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入deviceId"];
        return;
    }
    

    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:_deviceIDTextField.text forKey:@"deviceID"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] newPOST:postPemByDeviceId parameters:requestDic success:^(id responseObject) {
        SETUDValue(responseObject, @"RsaPublicKey");
        SETUDValue(self->_deviceIDTextField.text, @"LocaldeviceID");
        UDSYNC;
        [self regist];
        
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
    
    
    
   
}
- (void)regist{
    //    {
    //     "Username": "lkl",
    //     "Password": "123456",
    //     "LastName": "LastName",
    //     "FirstName": "FirstName",
    //     "Email": "Email",
    //     "Role": "Role"
    //    }
    
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:_firstNameTextField.text forKey:@"FirstName"];
    [requestDic setValue:_lastNameTextField.text forKey:@"LastName"];
    [requestDic setValue:_userNameTextField.text forKey:@"Username"];
    [requestDic setValue:_enailTextField.text forKey:@"Email"];
    [requestDic setValue:_passwordTextField.text forKey:@"Password"];
    [requestDic setValue:@"Role" forKey:@"Role"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:Postregister parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        if ([responseObject rangeOfString:@"Successfully"].location == NSNotFound) {
            [SVProgressHUD showErrorWithStatus:@"Register Successful"];
        }else{
            [SVProgressHUD showSuccessWithStatus:@"Register Successful"];
            [self performSelector:@selector(methodName) withObject:self afterDelay:1];
        }
        
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
}


- (IBAction)saomaClick:(id)sender {
    __weak typeof(self) weakSelf = self;
    AboutViewController *aboutVC = [[AboutViewController alloc] init];
    aboutVC.isLogin = @"login";
    aboutVC.comfireBlock = ^(NSString *result) {
        weakSelf.deviceIDTextField.text = result;
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





- (void)methodName{
    [self.navigationController popViewControllerAnimated:YES];
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

-(NSString *) utf8ToUnicode:(NSString *)string{
    NSUInteger length = [string length];
    NSMutableString *str = [NSMutableString stringWithCapacity:0];
    for (int i = 0;i < length; i++){
        NSMutableString *s = [NSMutableString stringWithCapacity:0];
        unichar _char = [string characterAtIndex:i];
        // 判断是否为英文和数字
        if (_char <= '9' && _char >='0'){
            [s appendFormat:@"%@",[string substringWithRange:NSMakeRange(i,1)]];
        }else if(_char >='a' && _char <= 'z'){
            [s appendFormat:@"%@",[string substringWithRange:NSMakeRange(i,1)]];
        }else if(_char >='A' && _char <= 'Z')
        {
            [s appendFormat:@"%@",[string substringWithRange:NSMakeRange(i,1)]];
        }else{
            // 中文和字符
            [s appendFormat:@"\\u%x",[string characterAtIndex:i]];
            // 不足位数补0 否则解码不成功
            if(s.length == 4) {
                [s insertString:@"00" atIndex:2];
            } else if (s.length == 5) {
                [s insertString:@"0" atIndex:2];
            }
        }
        [str appendFormat:@"%@", s];
    }
    return str;
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
