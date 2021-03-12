//
//  AboutViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/11/13.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "AboutViewController.h"
#import "SGQRCode.h"
#import "ScanSuccessJumpVC.h"
#import "MBProgressHUD+SGQRCode.h"

@interface AboutViewController (){
     SGQRCodeObtain *obtain;
}
@property (nonatomic, strong) SGQRCodeScanView *scanView;
@property (nonatomic, strong) UIButton *flashlightBtn;
@property (nonatomic, strong) UILabel *promptLabel;
@property (nonatomic, assign) BOOL isSelectedFlashlightBtn;
@property (nonatomic, strong) UIView *bottomView;
@end

@implementation AboutViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor blackColor];
    obtain = [SGQRCodeObtain QRCodeObtain];
    
    [self setupQRCodeScan];
    [self setupNavigationBar];
    [self.view addSubview:self.scanView];
    [self.view addSubview:self.promptLabel];
    /// 为了 UI 效果
    [self.view addSubview:self.bottomView];
}

- (void)viewWillAppear:(BOOL)animated {
    [super viewWillAppear:animated];

    /// 二维码开启方法
    [obtain startRunningWithBefore:nil completion:nil];
}
- (void)viewDidAppear:(BOOL)animated {
    [super viewDidAppear:animated];
    [self.scanView addTimer];
}

- (void)viewWillDisappear:(BOOL)animated {
    [super viewWillDisappear:animated];
    [self.scanView removeTimer];
    [self removeFlashlightBtn];
    [obtain stopRunning];
}

- (void)dealloc {
    NSLog(@"WCQRCodeVC - dealloc");
    [self removeScanningView];
}

- (void)setupQRCodeScan {
    __weak typeof(self) weakSelf = self;
    
    SGQRCodeObtainConfigure *configure = [SGQRCodeObtainConfigure QRCodeObtainConfigure];
    configure.sampleBufferDelegate = YES;
    [obtain establishQRCodeObtainScanWithController:self configure:configure];
    [obtain setBlockWithQRCodeObtainScanResult:^(SGQRCodeObtain *obtain, NSString *result) {
        if (result) {
            [MBProgressHUD SG_showMBProgressHUDWithModifyStyleMessage:@"正在处理..." toView:weakSelf.view];
            [obtain stopRunning];
            [obtain playSoundName:@"SGQRCode.bundle/sound.caf"];
            
            if ([weakSelf.isLogin isEqualToString:@"login"]) {
                if (weakSelf.comfireBlock != nil) {
                    weakSelf.comfireBlock(result);
                }
                [weakSelf.navigationController popViewControllerAnimated:YES];
            }else{
                ScanSuccessJumpVC *jumpVC = [[ScanSuccessJumpVC alloc] init];
                jumpVC.comeFromVC = ScanSuccessJumpComeFromWC;
                if ([result hasPrefix:@"http"]) {
                    jumpVC.jump_URL = result;
                }else{
                    jumpVC.jump_bar_code = result;
                }
                
                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.2 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
                    [MBProgressHUD SG_hideHUDForView:weakSelf.view];
                    [weakSelf.navigationController pushViewController:jumpVC animated:YES];
                });
            }
            
        }
    }];
    [obtain setBlockWithQRCodeObtainScanBrightness:^(SGQRCodeObtain *obtain, CGFloat brightness) {
        if (brightness < - 1) {
            [weakSelf.view addSubview:weakSelf.flashlightBtn];
        } else {
            if (weakSelf.isSelectedFlashlightBtn == NO) {
                [weakSelf removeFlashlightBtn];
            }
        }
    }];
}

- (void)setupNavigationBar {
    self.navigationItem.title = @"Scan";
}

- (SGQRCodeScanView *)scanView {
    if (!_scanView) {
        _scanView = [[SGQRCodeScanView alloc] initWithFrame:CGRectMake(0, 0, kScreenWidth, kScreenHeight)];
    }
    return _scanView;
}
- (void)removeScanningView {
    [self.scanView removeTimer];
    [self.scanView removeFromSuperview];
    self.scanView = nil;
}

- (UILabel *)promptLabel {
    if (!_promptLabel) {
        _promptLabel = [[UILabel alloc] init];
        _promptLabel.backgroundColor = [UIColor clearColor];
        CGFloat promptLabelX = 0;
        CGFloat promptLabelY = 0.73 * kScreenHeight;
        CGFloat promptLabelW = kScreenWidth;
        CGFloat promptLabelH = 25;
        _promptLabel.frame = CGRectMake(promptLabelX, promptLabelY, promptLabelW, promptLabelH);
        _promptLabel.textAlignment = NSTextAlignmentCenter;
        _promptLabel.font = [UIFont boldSystemFontOfSize:13.0];
        _promptLabel.textColor = [[UIColor whiteColor] colorWithAlphaComponent:0.6];
        _promptLabel.text = @"将二维码/条码放入框内, 即可自动扫描";
    }
    return _promptLabel;
}

- (UIView *)bottomView {
    if (!_bottomView) {
        _bottomView = [[UIView alloc] initWithFrame:CGRectMake(0, CGRectGetMaxY(self.scanView.frame), kScreenWidth, kScreenHeight - CGRectGetMaxY(self.scanView.frame))];
        _bottomView.backgroundColor = [[UIColor blackColor] colorWithAlphaComponent:0.5];
    }
    return _bottomView;
}

#pragma mark - - - 闪光灯按钮
- (UIButton *)flashlightBtn {
    if (!_flashlightBtn) {
        // 添加闪光灯按钮
        _flashlightBtn = [UIButton buttonWithType:(UIButtonTypeCustom)];
        CGFloat flashlightBtnW = 30;
        CGFloat flashlightBtnH = 30;
        CGFloat flashlightBtnX = 0.5 * (kScreenWidth - flashlightBtnW);
        CGFloat flashlightBtnY = 0.55 * kScreenHeight;
        _flashlightBtn.frame = CGRectMake(flashlightBtnX, flashlightBtnY, flashlightBtnW, flashlightBtnH);
        [_flashlightBtn setBackgroundImage:[UIImage imageNamed:@"SGQRCodeFlashlightOpenImage"] forState:(UIControlStateNormal)];
        [_flashlightBtn setBackgroundImage:[UIImage imageNamed:@"SGQRCodeFlashlightCloseImage"] forState:(UIControlStateSelected)];
        [_flashlightBtn addTarget:self action:@selector(flashlightBtn_action:) forControlEvents:UIControlEventTouchUpInside];
    }
    return _flashlightBtn;
}

- (void)flashlightBtn_action:(UIButton *)button {
    if (button.selected == NO) {
        [obtain openFlashlight];
        self.isSelectedFlashlightBtn = YES;
        button.selected = YES;
    } else {
        [self removeFlashlightBtn];
    }
}

- (void)removeFlashlightBtn {
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.2 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [obtain closeFlashlight];
        self.isSelectedFlashlightBtn = NO;
        self.flashlightBtn.selected = NO;
        [self.flashlightBtn removeFromSuperview];
    });
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
