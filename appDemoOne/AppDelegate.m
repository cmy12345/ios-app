//
//  AppDelegate.m
//  appDemoOne
//
//  Created by wendf on 2020/11/12.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "AppDelegate.h"
#import "LoginViewController.h"
#import "DDRSAWrapper+openssl.h"

@interface AppDelegate ()

@end

@implementation AppDelegate


- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    // Override point for customization after application launch.
     [self SVProgressHUDSetting];
    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    
    LoginViewController *loginVC = [[LoginViewController alloc] init];
    UINavigationController *nav = [[UINavigationController alloc] initWithRootViewController:loginVC];
    self.window.rootViewController = nav;
    [self opensslGenerate];
    [self.window makeKeyAndVisible];
    return YES;
}
/**本地生成rsa秘钥对*/
- (void)opensslGenerate{
    [SVProgressHUD show];
    RSA *publicKey;
    RSA *privateKey;
    NSString *_publicKeyBase64;
    NSString *_privateKeyBase64;
    if ([DDRSAWrapper generateRSAKeyPairWithKeySize:1024 publicKey:&publicKey privateKey:&privateKey]) {
        [SVProgressHUD dismiss];
//        char * m = [DDRSAWrapper openssl_modFromKey:publicKey];
//        char * e = [DDRSAWrapper openssl_expFromPublicKey:publicKey];
//        char * d = [DDRSAWrapper openssl_expFromPrivateKey:privateKey];
        
        _publicKeyBase64 =[[DDRSAWrapper base64EncodedStringPublicKey:publicKey] stringByReplacingOccurrencesOfString:@"\n" withString:@""];
        _privateKeyBase64 = [[DDRSAWrapper base64EncodedStringPrivateKey:privateKey] stringByReplacingOccurrencesOfString:@"\n" withString:@""];
        
        NSLog(@"_publicKeyBase64:%@ \n",_publicKeyBase64);
        NSLog(@"_privateKeyBase64:%@ \n",_privateKeyBase64);
        SETUDValue(_publicKeyBase64, @"localPublicKey");
        SETUDValue(_privateKeyBase64, @"localPrivateKey");
        UDSYNC;
//        NSString *logText = [NSString stringWithFormat:@"openssl 生成密钥成功！\n模数：%s\n公钥指数：%s\n私钥指数：%s",m,e,d];
//        [self addlogText:logText];
    }else{
        [SVProgressHUD showErrorWithStatus:@"生成秘钥对失败，请重启APP"];
    }
}


/**
 设置SVProgressHUD默认属性
 */
- (void)SVProgressHUDSetting{
    //设置HUD的Style
    [SVProgressHUD setDefaultStyle:SVProgressHUDStyleDark];
    [SVProgressHUD setMinimumDismissTimeInterval:1.0];
    [SVProgressHUD setDefaultMaskType:SVProgressHUDMaskTypeBlack];
}

@end
