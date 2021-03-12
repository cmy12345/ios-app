//
//  MenuView.h
//  GXAlertSample
//
//  Created by Gin on 2020/3/25.
//  Copyright © 2020 gin. All rights reserved.
//

#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

typedef void(^itemClickBlock)(NSIndexPath* indexPath);

@interface MenuView : UIView

@property (nonatomic , copy) itemClickBlock itemClickBlock;

@end

NS_ASSUME_NONNULL_END
