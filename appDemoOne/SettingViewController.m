//
//  SettingViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/11/13.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

static NSString *QiInputCorrectionLevelL = @"L";//!< L: 7%
static NSString *QiInputCorrectionLevelM = @"M";//!< M: 15%
static NSString *QiInputCorrectionLevelQ = @"Q";//!< Q: 25%
static NSString *QiInputCorrectionLevelH = @"H";//!< H: 30%


#import "SettingViewController.h"

@interface SettingViewController ()
@property (weak, nonatomic) IBOutlet UITextField *contentTextField;
@property (weak, nonatomic) IBOutlet UIImageView *imageView;

@end

@implementation SettingViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"Generate QR Code";
}
- (IBAction)comfireBtnClick:(id)sender {
    if (![self isBlankString:_contentTextField.text]) {
        self.imageView.image = [self generateQRCodeWithInputMessage:_contentTextField.text Width:260.0 Height:260.0];
    }
}

- (UIImage *)generateQRCodeWithInputMessage:(NSString *)inputMessage
                                      Width:(CGFloat)width
                                     Height:(CGFloat)height{
    NSData *inputData = [inputMessage dataUsingEncoding:NSUTF8StringEncoding];
    CIFilter *filter = [CIFilter filterWithName:@"CIQRCodeGenerator"];
    [filter setValue:inputData forKey:@"inputMessage"];
    CIImage *ciImage = filter.outputImage;
    // 消除模糊
    CGFloat scaleX = MIN(width, height)/ciImage.extent.size.width;
    CGFloat scaleY = MIN(width, height)/ciImage.extent.size.height;
    ciImage = [ciImage imageByApplyingTransform:CGAffineTransformScale(CGAffineTransformIdentity, scaleX, scaleY)];
    UIImage *returnImage = [UIImage imageWithCIImage:ciImage];
    return returnImage;
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
