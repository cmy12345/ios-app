//
//  Api.h
//  appDemoOne
//
//  Created by wendf on 2020/11/14.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#ifndef Api_h
#define Api_h


#define DXBASE_URL @"http://10.180.103.9:9068"
//@"http://picharger01.www.mplabcharger.org:9063"
//@"http://10.180.103.9:9068"
//@"http://picharger01.www.mplabcharger.org:9063"
/**
 * 登录
 */
#define PostLogin \
CONTACT(DXBASE_URL, @"/mobile/UserInfo/LoginCheck")

/**
 *注册接口
 */
#define Postregister \
CONTACT(DXBASE_URL, @"/mobile/UserInfo/SendtoPeer")


/**
 *退出登录接口
 */
#define PostLogout \
CONTACT(DXBASE_URL, @"/mobile/UserInfo/Logout")


/**
 图表
 */
#define PostChart \
CONTACT(DXBASE_URL, @"/mobile/showTables")

/**
 *
 */
#define PostShowSellEngine \
CONTACT(DXBASE_URL, @"/mobile/showEVStatus")

/**
 *
 */
#define PostBuyPower \
CONTACT(DXBASE_URL, @"/mobile/Service/BuyPower")


/**
 *
 */
#define PostSellPower \
CONTACT(DXBASE_URL, @"/mobile/Service/SellPower")

/**
 *获取公钥
 */
#define postPemByDeviceId \
CONTACT(DXBASE_URL, @"/mobile/getPemByDeviceId")




#endif /* Api_h */
