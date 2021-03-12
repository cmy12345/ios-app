//
//  BuyEnergyViewController.m
//  appDemoOne
//
//  Created by wendf on 2020/12/7.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "BuyEnergyViewController.h"
#import "HXCharts.h"

@interface BuyEnergyViewController ()
@property (weak, nonatomic) IBOutlet UIScrollView *myScrollView;
@property (weak, nonatomic) IBOutlet UIView *chartView;
@property (nonatomic, strong)HXBarChart *bar;
@property (weak, nonatomic) IBOutlet UILabel *charingStatusLabel1;
@property (weak, nonatomic) IBOutlet UILabel *charingStatusLabel2;
@property (weak, nonatomic) IBOutlet UILabel *charingStatusLabel3;
@property (weak, nonatomic) IBOutlet UILabel *charingStatusLabel4;
@property (weak, nonatomic) IBOutlet UILabel *charingStatusLabel5;
@property (weak, nonatomic) IBOutlet UIButton *choice1;
@property (weak, nonatomic) IBOutlet UIButton *choice2;
@property (weak, nonatomic) IBOutlet UIButton *choice3;
@property (weak, nonatomic) IBOutlet UITextField *textField;
@property (weak, nonatomic) IBOutlet UIButton *submitBtn;
@property (weak, nonatomic) IBOutlet UIView *buyEngeryView;

@property (weak, nonatomic) IBOutlet UIView *sellEngeryView;
@property (weak, nonatomic) IBOutlet UITextField *sellTextField3;
@property (weak, nonatomic) IBOutlet UIButton *sellBtn1;
@property (weak, nonatomic) IBOutlet UIButton *sellBtn2;

@property (weak, nonatomic) IBOutlet UILabel *typelabel;

@property (nonatomic)NSString *choiceStr;
@property (nonatomic)NSString *sellChoiceStr;
@property (nonatomic, strong)NSArray *chartDataArray;
@property (nonatomic, strong)NSArray *centerDataArray;

@end

@implementation BuyEnergyViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.choiceStr = @"";
    self.sellChoiceStr = @"";
    // Do any additional setup after loading the view from its nib.
    [self requestData];
    [self requestCenterData];
    if ([self.typeStr isEqualToString:@"sellView"]) {
        self.sellEngeryView.hidden = NO;
        self.buyEngeryView.hidden = YES;
        self.typelabel.text = @"Sell Energy";
    }else if ([self.typeStr isEqualToString:@"buyView"]){
        self.buyEngeryView.hidden = NO;
        self.sellEngeryView.hidden = YES;
        self.typelabel.text = @"Buy Energy";
    }
}

-(void)requestData{
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
//    [requestDic setValue:_phoneTextField.text forKey:@"Username"];
//    [requestDic setValue:_passwordTextField.text forKey:@"Password"];
//    [requestDic setValue:@"123" forKey:@"deviceID"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:PostChart parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        NSLog(@"%@",responseObject);
        self->_chartDataArray = responseObject;
        [self createChart];
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
}
-(void)requestCenterData{
     __weak typeof(self) weakSelf = self;
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:PostShowSellEngine parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        NSLog(@"%@",responseObject);
        self->_centerDataArray = responseObject;
        [weakSelf fiilCenterData];
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
}
- (void)fiilCenterData{
    if (_centerDataArray && _centerDataArray.count > 0) {
        self.charingStatusLabel1.text =[NSString stringWithFormat:@"%@",_centerDataArray[0][0]];
        self.charingStatusLabel2.text =[NSString stringWithFormat:@"%@",_centerDataArray[0][1]];
        self.charingStatusLabel3.text =[NSString stringWithFormat:@"%@",_centerDataArray[0][2]];
        self.charingStatusLabel4.text =[NSString stringWithFormat:@"%@",_centerDataArray[0][3]];
        self.charingStatusLabel5.text =[NSString stringWithFormat:@"%@",_centerDataArray[0][4]];
    }
}
//sell
- (IBAction)sellbtn1Click:(UIButton *)sender {
    NSInteger tag = sender.tag - 2000;
    [self sellchoice:tag];
}

- (IBAction)sellBtn2Click:(UIButton *)sender {
    NSInteger tag = sender.tag - 2000;
    [self sellchoice:tag];
}


- (IBAction)sellsumitBtnClick:(id)sender {
    
    if ([self isBlankString:self.sellTextField3.text]) {
        [SVProgressHUD showInfoWithStatus:@"Activity"];
        return;
    }
    if ([self isBlankString:self.sellChoiceStr]) {
        [SVProgressHUD showInfoWithStatus:@"Property"];
        return;
    }
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:self.sellTextField3.text forKey:@"value"];
    [requestDic setValue:self.sellChoiceStr forKey:@"hours"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:PostSellPower parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        NSLog(@"%@",responseObject);
        [SVProgressHUD showSuccessWithStatus:@"submit successful"];
//        if ([responseObject isEqualToString:[NSString stringWithFormat:@"\"%@\"",@"success"]]) {
//            [SVProgressHUD showSuccessWithStatus:@"提交成功"];
//        }else{
//            [SVProgressHUD showErrorWithStatus:@"提交失败"];
//        }
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
    
}
-(void)sellchoice:(NSInteger)tag{
    switch (tag) {
        case 1:
        {
            self.sellBtn1.backgroundColor = [UIColor orangeColor];
            self.sellBtn2.backgroundColor = [UIColor grayColor];
            self.sellChoiceStr = @"1";
        }
            break;
            case 2:
        {
            self.sellBtn2.backgroundColor = [UIColor orangeColor];
            self.sellBtn1.backgroundColor = [UIColor grayColor];
            self.sellChoiceStr = @"2";
        }
            break;
        default:
            break;
    }
}

//buy
- (IBAction)submitBtnClick:(id)sender {
    if ([self isBlankString:self.choiceStr]) {
        [SVProgressHUD showInfoWithStatus:@"请选择····"];
        return;
    }
    if ([self isBlankString:self.textField.text]) {
        [SVProgressHUD showInfoWithStatus:@"请输入活动类型"];
        return;
    }
    
    NSMutableDictionary *requestDic = [NSMutableDictionary dictionary];
    [requestDic setValue:self.choiceStr forKey:@"method"];
    [requestDic setValue:self.textField.text forKey:@"amount"];
    [SVProgressHUD show];
    [[DXNetworkCenter managerDXNetwork] POST:PostBuyPower parameters:requestDic success:^(id responseObject) {
        [SVProgressHUD dismiss];
        NSLog(@"%@",responseObject);
//        if ([responseObject isEqualToString:[NSString stringWithFormat:@"\"%@\"",@"success"]]) {
//            [SVProgressHUD showSuccessWithStatus:@"提交成功"];
//        }else{
//            [SVProgressHUD showErrorWithStatus:@"提交失败"];
//        }
        [SVProgressHUD showSuccessWithStatus:@"提交成功"];
    } failure:^(id responseObject) {
        [SVProgressHUD showErrorWithStatus:responseObject];
    }];
}
- (IBAction)choice1BtnClick:(UIButton *)sender {
    NSInteger tag = sender.tag - 1000;
    [self choice:tag];
}
- (IBAction)choice2BtnClick:(UIButton *)sender {
    NSInteger tag = sender.tag - 1000;
    [self choice:tag];
}
- (IBAction)choice3BtnClick:(UIButton *)sender {
    NSInteger tag = sender.tag - 1000;
    [self choice:tag];
}
-(void)choice:(NSInteger)tag{
    switch (tag) {
        case 1:
        {
            self.choice1.backgroundColor = [UIColor orangeColor];
            self.choice2.backgroundColor = [UIColor grayColor];
            self.choice3.backgroundColor = [UIColor grayColor];
            self.choiceStr = @"1";
        }
            break;
            case 2:
        {
            self.choice2.backgroundColor = [UIColor orangeColor];
            self.choice1.backgroundColor = [UIColor grayColor];
            self.choice3.backgroundColor = [UIColor grayColor];
            self.choiceStr = @"2";
        }
            break;
            case 3:
        {
            self.choice3.backgroundColor = [UIColor orangeColor];
            self.choice2.backgroundColor = [UIColor grayColor];
            self.choice1.backgroundColor = [UIColor grayColor];
            self.choiceStr = @"3";
        }
            break;
        default:
            break;
    }
}

- (void)createChart{
    CGFloat width = self.view.frame.size.width;
    CGFloat barChartWidth = self.view.frame.size.width;
    CGFloat barChartHeight = 350;
    
    CGFloat barChartX = (width - barChartWidth) / 2;
    CGFloat barChartY = 30;
    
    ///渐变色
    NSArray *color1 = @[[self colorWithHexString:@"#07B2F6" alpha:1],[self colorWithHexString:@"#06A0DD" alpha:1]];
    
    _bar = [[HXBarChart alloc] initWithFrame:CGRectMake(barChartX, barChartY, barChartWidth, barChartHeight) withMarkLabelCount:6 withOrientationType:OrientationVertical];
    _bar.backgroundColor = [UIColor whiteColor];
    [self.chartView addSubview:_bar];
    if (_chartDataArray && _chartDataArray.count > 0) {
        _bar.titleArray = _chartDataArray[1];
        _bar.valueArray = _chartDataArray[0];
        NSMutableArray *colorArray = [[NSMutableArray alloc] init];
        for (int i = 0; i <  _bar.titleArray.count; i++) {
            [colorArray addObject:color1];
        }
        _bar.colorArray = colorArray;
        _bar.locations = @[@0.15,@0.85];
        _bar.markTextColor = [UIColor grayColor];
        _bar.markTextFont = [UIFont systemFontOfSize:14];
        _bar.xlineColor = [self colorWithHexString:@"#4b4e52" alpha:1];
        ///不需要滑动可不设置
        _bar.contentValue = 7 * 45;
        _bar.barWidth = 25;
        _bar.margin = 50;
        
        [_bar drawChart];
    }
    
}
#pragma mark 设置16进制颜色
- (UIColor *)colorWithHexString:(NSString *)color alpha:(CGFloat)alpha{
    //删除字符串中的空格
    NSString *cString = [[color stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]] uppercaseString];
    // String should be 6 or 8 characters
    if ([cString length] < 6)
    {
        return [UIColor clearColor];
    }
    // strip 0X if it appears
    //如果是0x开头的，那么截取字符串，字符串从索引为2的位置开始，一直到末尾
    if ([cString hasPrefix:@"0X"])
    {
        cString = [cString substringFromIndex:2];
    }
    //如果是#开头的，那么截取字符串，字符串从索引为1的位置开始，一直到末尾
    if ([cString hasPrefix:@"#"])
    {
        cString = [cString substringFromIndex:1];
    }
    if ([cString length] != 6)
    {
        return [UIColor clearColor];
    }
    
    // Separate into r, g, b substrings
    NSRange range;
    range.location = 0;
    range.length = 2;
    //r
    NSString *rString = [cString substringWithRange:range];
    //g
    range.location = 2;
    NSString *gString = [cString substringWithRange:range];
    //b
    range.location = 4;
    NSString *bString = [cString substringWithRange:range];
    
    // Scan values
    unsigned int r, g, b;
    [[NSScanner scannerWithString:rString] scanHexInt:&r];
    [[NSScanner scannerWithString:gString] scanHexInt:&g];
    [[NSScanner scannerWithString:bString] scanHexInt:&b];
    return [UIColor colorWithRed:((float)r / 255.0f) green:((float)g / 255.0f) blue:((float)b / 255.0f) alpha:alpha];
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

//-(void)viewDidAppear:(BOOL)animated{
//    [super viewDidAppear:animated];
//    self.myScrollView.contentSize = CGSizeMake(kScreenWidth,1000);
//}
/*
#pragma mark - Navigation

// In a storyboard-based application, you will often want to do a little preparation before navigation
- (void)prepareForSegue:(UIStoryboardSegue *)segue sender:(id)sender {
    // Get the new view controller using [segue destinationViewController].
    // Pass the selected object to the new view controller.
}
*/

@end
