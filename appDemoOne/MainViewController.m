//
//  MainViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/11/13.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//


#import "MenuView.h"
#import "UIView+GXAlertView.h"
#import "MainViewController.h"
#import "AboutViewController.h"
#import "SettingViewController.h"
#import "LoginViewController.h"
#import <AVFoundation/AVFoundation.h>
#import "BuyEnergyViewController.h"
@interface MainViewController ()

@property (nonatomic, strong)MenuView *menu;

@end

@implementation MainViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    [self createNav];
    kWeakSelf(weakSelf);
    self.menu.itemClickBlock = ^(NSIndexPath *indexPath) {
        switch (indexPath.row) {
            case 0:
                [weakSelf itemClick0];
                break;
            case 1:
                [weakSelf itemClick1];
                break;
            case 2:
                [weakSelf itemClick2];
                break;
            case 3:
                [weakSelf itemClick3];
                break;
            case 4:
                [weakSelf itemClick4];
                break;
            default:
                break;
        }
    };
    
}
- (void)createNav{
    UIButton *btn = [UIButton buttonWithType:UIButtonTypeSystem];
    [btn setBackgroundImage:[UIImage imageNamed:@"category"] forState:UIControlStateNormal];
    [btn addTarget:self action:@selector(leftBtnClik:) forControlEvents:UIControlEventTouchUpInside];
    UIBarButtonItem *leftItem = [[UIBarButtonItem alloc]initWithCustomView:btn];
//    leftItem.imageInsets = UIEdgeInsetsMake(0, -15,0, 0);//设置向左偏移
    self.navigationItem.leftBarButtonItem = leftItem;
}

- (void)leftBtnClik:(UIButton *)sender {
    [self.menu showAlertStyle:GXAlertStyleSheetLeft backgoundTapDismissEnable:YES usingSpring:YES];
}
- (void)itemClick0{
    [_menu hideToView];
}
- (void)itemClick1{
    [_menu hideToView];
    BuyEnergyViewController *vc = [[BuyEnergyViewController alloc] init];
    vc.typeStr = @"sellView";
    [self.navigationController pushViewController:vc animated:YES];
    
}
- (void)itemClick2{
    [_menu hideToView];
    AboutViewController *aboutVC = [[AboutViewController alloc] init];
    [self QRCodeScanVC:aboutVC];
}
- (void)itemClick3{
    [_menu hideToView];
    SettingViewController *settingVC = [[SettingViewController alloc] init];
    [self.navigationController pushViewController:settingVC animated:YES];
}
- (void)itemClick4{
    for (UIView *v in [UIApplication sharedApplication].keyWindow.subviews) {
        [v removeFromSuperview];
    }
    LoginViewController *loginVC = [[LoginViewController alloc] init];
    UINavigationController *nav = [[UINavigationController alloc] initWithRootViewController:loginVC];
    [UIApplication sharedApplication].keyWindow.rootViewController = nav;
}
- (IBAction)buyEnergy:(id)sender {
    BuyEnergyViewController *vc = [[BuyEnergyViewController alloc] init];
    vc.typeStr = @"buyView";
    [self.navigationController pushViewController:vc animated:YES];
}

- (IBAction)logoutBtnClick:(id)sender {
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:UDValue(@"myphone") ? UDValue(@"myphone") : @"" forKey:@"Username"];
    [requestDic setValue:UDValue(@"mydeviceId") ? UDValue(@"mydeviceId") : @"" forKey:@"deviceID"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:PostLogout parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        if ([responseObject rangeOfString:@"Successfully"].location == NSNotFound) {
            [SVProgressHUD showErrorWithStatus:@"Logout Failed"];
        }else{
            [SVProgressHUD showSuccessWithStatus:@"Logout Successful"];
            for (UIView *v in [UIApplication sharedApplication].keyWindow.subviews) {
                [v removeFromSuperview];
            }
            LoginViewController *loginVC = [[LoginViewController alloc] init];
            UINavigationController *nav = [[UINavigationController alloc] initWithRootViewController:loginVC];
            [UIApplication sharedApplication].keyWindow.rootViewController = nav;
        }
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
    
}


- (MenuView *)menu{
    if (_menu == nil) {
        _menu = [[MenuView alloc] initWithFrame:CGRectMake(0, 0, 300, kScreenHeight)];
    }
    return _menu;
}

- (IBAction)firstBtnClick:(id)sender {
    BuyEnergyViewController *vc = [[BuyEnergyViewController alloc] init];
    vc.typeStr = @"sellView";
    [self.navigationController pushViewController:vc animated:YES];
}
- (IBAction)secondBtnClick:(id)sender {
    AboutViewController *aboutVC = [[AboutViewController alloc] init];
    [self QRCodeScanVC:aboutVC];
    
}
- (IBAction)thirdBtnClick:(id)sender {
    SettingViewController *settingVC = [[SettingViewController alloc] init];
    [self.navigationController pushViewController:settingVC animated:YES];
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

/*
#pragma mark - Navigation

// In a storyboard-based application, you will often want to do a little preparation before navigation
- (void)prepareForSegue:(UIStoryboardSegue *)segue sender:(id)sender {
    // Get the new view controller using [segue destinationViewController].
    // Pass the selected object to the new view controller.
}
*/

@end
