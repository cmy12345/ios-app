//
//  AboutViewController.h
//  appDemoOne
//
//  Created by wendf on 2020/11/13.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import <UIKit/UIKit.h>

typedef void(^comfireBtnBlock)(NSString *result);

@interface AboutViewController : UIViewController

@property (nonatomic, copy)NSString* isLogin;

@property (nonatomic , copy) comfireBtnBlock comfireBlock;

@end
