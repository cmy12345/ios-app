/*
 @author: ideawu
 @link: https://github.com/ideawu/Objective-C-RSA
*/


/**
 //测试要加密的数据
 NSString *sourceStr = @"iOS端RSA加密";
 //公钥加密
 NSString *encryptStr = [RSA encryptString:sourceStr publicKey:publicKey];
 //私钥解密
 NSString *decrypeStr = [RSA decryptString:encryptStr privateKey:privateKey];
 
 
 //私钥加密
 NSString *encryptStr1 = [RSA encryptString:sourceStr privateKey:privateKey];
 //公钥解密
 NSString *decrypeStr1 = [RSA decryptString:encryptStr1 publicKey:publicKey];
 */

#import <Foundation/Foundation.h>

@interface RSAUtil : NSObject

// return base64 encoded string
+ (NSString *)encryptString:(NSString *)str publicKey:(NSString *)pubKey;
// return raw data
+ (NSData *)encryptData:(NSData *)data publicKey:(NSString *)pubKey;
// return base64 encoded string
+ (NSString *)encryptString:(NSString *)str privateKey:(NSString *)privKey;
// return raw data
+ (NSData *)encryptData:(NSData *)data privateKey:(NSString *)privKey;

// decrypt base64 encoded string, convert result to string(not base64 encoded)
+ (NSString *)decryptString:(NSString *)str publicKey:(NSString *)pubKey;
+ (NSData *)decryptData:(NSData *)data publicKey:(NSString *)pubKey;
+ (NSString *)decryptString:(NSString *)str privateKey:(NSString *)privKey;
+ (NSData *)decryptData:(NSData *)data privateKey:(NSString *)privKey;

@end
