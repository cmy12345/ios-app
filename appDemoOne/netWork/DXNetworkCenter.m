//
//  DXNetworkCenter.m
//  UserRetention
//
//  Created by wendf on 2020/4/21.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "DXNetworkCenter.h"
#import "RSAUtil.h"
#import <CommonCrypto/CommonDigest.h>
#import <CommonCrypto/CommonCrypto.h>
#import "DDRSAWrapper+openssl.h"
static CGFloat const kDefaultTimeoutInterval = 30.0f;    // 默认超时时间是30秒

////加密传给后端参数 key
//static NSString * const APPRsaPublicKey = @"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDY2rBVtB1JEoWBEZjAU6X0KoR2UbXrtqA+LrH/PCbZQbB3rZGF2gswG6SbIHoucWvqMkr3yV4ZZn1jukZs2wiqjsBK3IDt5O3gQfzGa73xAtlQoyXwz9OqLDiuUoKSb0yRqbevMSPUE60s1Zm0T1sMK+54kxrfU5erCVKvlPU/GQIDAQAB";
//
////解密请求结果key
//static NSString * const APPRsaPrivateKey = @"MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBANjasFW0HUkShYERmMBTpfQqhHZRteu2oD4usf88JtlBsHetkYXaCzAbpJsgei5xa+oySvfJXhlmfWO6RmzbCKqOwErcgO3k7eBB/MZrvfEC2VCjJfDP06osOK5SgpJvTJGpt68xI9QTrSzVmbRPWwwr7niTGt9Tl6sJUq+U9T8ZAgMBAAECgYEA19u4M1d630YEhpnRh4C8bPP1ryFfCSddEwjAPeTOduygkEDB3o9RG64oiBIoDRrx5MnzPfvAI2CV6DN/7tOJJwc7YSzY+rJcZeBKtx9AHhUkFW7Hdi/afC14ejVVKeav0fjlO8/SspCwDgMW2FMIbp706pguiA3PbeoDfNKYHRECQQD+rgp24uZdqIE3D7JhBIJDSycHmHYqWFTLbZAANf6jyaGiDdL4tAG4RawH/wYwaJxsQGN8xz+nYUuH0XloWazXAkEA2fp0Gfs9NtgGqquv/4UQC1DHGT/iwCnt86KLF/TVvPAjVxO3kGxr/A0kNfQbgUDiBjUx3vWdRQ4AeLF76D6FjwJBAOuwUQrYzOwcBwjXw/K443w3TnVfCOwDNuXUDRHE5lTZQnXgaT+0BmtsPtpfjnC6PxiHNgrBsgzKo8Wbe8mwQ50CQDDL11fFnWN8oqlsO774u6m80IU/fvRDrqf+uCKJxZtBKrggitRC4T2Qd424crvRmYeIOvzNgQJnawWZvcI01NMCQAlCEuVFjiSYnzORLfXbQdKRqzZ5tmMDTJaYkDj7GhQvg0zgbIFFmUu2SgdEuAf35H4r42G7Em2eSEEmlBujBtw=";



//static NSString * const APPRsaPublicKey = @"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnjw7D9BWkukha0KHkHKxDCTJEpgQzibVGl92VvZiWtfAe733zCARKuv2qfkLbcRsfvNqiASrZs5J07EqFNWDrGh5HjCfOyEO1FONxscQEgsrFCI4PMbz/LYR66zcldHmI6+K9MmwB1gTl23KMsmQDAusQXOkO7CFtrggeGT1/vwIDAQAB";
//
////解密请求结果key
//static NSString * const APPRsaPrivateKey = @"MIICXAIBAAKBgQCnjw7D9BWkukha0KHkHKxDCTJEpgQzibVGl92VvZiWtfAe733zCARKuv2qfkLbcRsfvNqiASrZs5J07EqFNWDrGh5HjCfOyEO1FONxscQEgsrFCI4PMbz/LYR66zcldHmI6+K9MmwB1gTl23KMsmQDAusQXOkO7CFtrggeGT1/vwIDAQABAoGAS9Gw9bxB+usMCIP1bXoH/MFxjJyus/9xFoNrkfFb1X54LBdkn48WGhao5/gAGroAcwkKyVnL4Pyfnea6BbLUqnHd5VNrZM6P2bCovWKzBGj4HPIibICAoCtP2XSHkZ/KORXBy12vPVEI+eX4hnYEEEqUPE9HtquGh8NaVgP5mPkCQQDZPiAk4tjuoui+6VtMWRmOFaWzd4MhlqJnADg9q6C1G9VDKVllWiBWB2FEoRGc8q1HY7QoCzndSIcJUQN6dZfzAkEAxXPHSzl1sw1MnKycBDpvpdgYBLcd5PW2PFfLwHervOg0Vj/Q1dx6wsuoFAfWK52H/GyVMc0/28rTynKRB/JYBQJARypn402A3SP29NuDMg6aJYaH4rPK/EzZZL6YrfM0UUAN69N22pHct/Hw9keBepWxGArccKXEze29dtrYNdyh6wJAMEosh306B9xMzFR6o54XCBxdY2nVadWeCAwAzMV3vu+bPSzGSkdtzo44QQ3ZlzkjtNxpcJCd+YcVXQG/7o2acQJBAKq8CH8QYuk16M6sAUTNVcfmWPLxUq20q1VmktJzn8WZk2u43Y0AjjShuU51gp0VoFnUN1bgqLiRinPxaJnf8ZE=";


@implementation DXNetworkCenter

+ (instancetype)managerDXNetwork{
    DXNetworkCenter *manager = [DXNetworkCenter manager];
    
    
    manager.requestSerializer = [AFJSONRequestSerializer serializer];
    manager.responseSerializer = [AFHTTPResponseSerializer serializer];
    manager.requestSerializer.timeoutInterval = kDefaultTimeoutInterval;
    [manager.requestSerializer setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];

    manager.responseSerializer.acceptableContentTypes = [NSSet setWithObjects:@"text/html", @"text/plain", @"application/json", @"text/json",@"text/javascript", nil];
    
    /************************* header *********************/
    NSString *public_pem = UDValue(@"localPublicKey") ? UDValue(@"localPublicKey") : @"";
    NSString *deviceId = UDValue(@"LocaldeviceID") ? UDValue(@"LocaldeviceID") : @"";
    [manager.requestSerializer setValue:public_pem forHTTPHeaderField:@"public_pem"];
    [manager.requestSerializer setValue:deviceId forHTTPHeaderField:@"deviceId"];
    /************************* header *********************/
    
    
    return manager;
}

//- (NSURLSessionDataTask *)GET:(NSString *)URLString
//                   parameters:(id)parameters
//                      success:(void (^)(DXNetworkResponse *responseObject))success
//                      failure:(void (^)(DXNetworkResponse *responseObject, NSError *error))failure{
//    return [super GET:URLString parameters:parameters progress:^(NSProgress * _Nonnull downloadProgress) {
//
//    } success:^(NSURLSessionDataTask * _Nonnull task, id  _Nullable responseObject) {
//        NSLog(@"请求地址---->%@\n请求参数---->%@\n请求返回---->%@\n",URLString,parameters,responseObject);
//        DXNetworkResponse *resp = [DXNetworkResponse requestSuccessProcessorTask:responseObject response:responseObject];
//        if (resp.responseType == DXNetworkResponseTypeSuccess) { // 业务逻辑
//            if (success) success(resp);
//        } else {
//            if (failure) failure(resp, nil);
//        }
//    } failure:^(NSURLSessionDataTask * _Nullable task, NSError * _Nonnull error) {
//        NSLog(@"请求地址---->%@\n请求参数---->%@\n请求返回---->%@\n",URLString,parameters,error);
//        if (failure) failure([DXNetworkResponse requestFailedProcessorTask:task response:error], error);
//    }];
//}

- (NSURLSessionDataTask *)POST:(NSString *)URLString
                    parameters:(id)parameters
                       success:(void (^)(id responseObject))success
                       failure:(void (^)(id responseObject))failure{
//    NSString *public_pem = UDValue(@"localPublicKey") ? UDValue(@"localPublicKey") : @"";
//    NSMutableDictionary *requestDic = [NSMutableDictionary dictionaryWithDictionary:parameters];
//    [requestDic setValue:public_pem forKey:@"public_pem_key"];
    
    NSDictionary *param = [self RSADictionary:parameters];
    
    return [super POST:URLString parameters:param progress:^(NSProgress * _Nonnull uploadProgress) {
        
    } success:^(NSURLSessionDataTask * _Nonnull task, id  _Nullable responseObject) {
        
        
        if ([URLString isEqualToString:PostChart] || [URLString isEqualToString:PostShowSellEngine]) {
            
            NSString * jsonStr = [self URLDecodedString:[[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding]];
//            NSString *resultStr = [RSAUtil decryptString:jsonStr privateKey:APPRsaPrivateKey];
            NSString *resultStr = [self opensslPrivateKeyDecrypt:jsonStr];
            
            NSArray *result = [self arrayWithJsonString:resultStr];
            if (success) success(result);
            NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,param,result);
        }else if ([URLString isEqualToString:PostLogin] || [URLString isEqualToString:PostBuyPower] || [URLString isEqualToString:PostSellPower] || [URLString isEqualToString:Postregister]|| [URLString isEqualToString:PostLogout]){
            NSString * jsonStr = [self URLDecodedString:[[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding]];
//            NSString *resultStr = [RSAUtil decryptString:jsonStr privateKey:APPRsaPrivateKey];
            NSString *resultStr = [self opensslPrivateKeyDecrypt:jsonStr];
            if (success) success(resultStr);
            NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,param,resultStr);
        }
        
        
    } failure:^(NSURLSessionDataTask * _Nullable task, NSError * _Nonnull error) {
        
        NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,param,error);
        if (error) {
//            NSHTTPURLResponse *response = (NSHTTPURLResponse *)task.response;
//            NSInteger httpStatus = response.statusCode;
            if (failure) failure(error.localizedDescription);
        }
    }];
}

- (NSURLSessionDataTask *)newPOST:(NSString *)URLString
                    parameters:(id)parameters
                       success:(void (^)(id responseObject))success
                       failure:(void (^)(id responseObject))failure{
//    NSString *public_pem = UDValue(@"localPublicKey") ? UDValue(@"localPublicKey") : @"";
//    NSMutableDictionary *requestDic = [NSMutableDictionary dictionaryWithDictionary:parameters];
//    [requestDic setValue:public_pem forKey:@"public_pem_key"];
    
    return [super POST:URLString parameters:parameters progress:^(NSProgress * _Nonnull uploadProgress) {
        
    } success:^(NSURLSessionDataTask * _Nonnull task, id  _Nullable responseObject) {
        NSLog(@"\n response %@",task.originalRequest.allHTTPHeaderFields);
//        NSString * jsonStr = [[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding];
        NSString * jsonStr = [self URLDecodedString:[[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding]];
        
        NSString *resultStr = [self opensslPrivateKeyDecrypt:jsonStr];
        
        if (success) success(resultStr);
        
        
//        if ([URLString isEqualToString:PostChart] || [URLString isEqualToString:PostShowSellEngine]) {
//
//            NSString * jsonStr = [self URLDecodedString:[[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding]];
//            NSString *resultStr = [RSA decryptString:jsonStr privateKey:APPRsaPrivateKey];
//            NSArray *result = [self arrayWithJsonString:resultStr];
//            if (success) success(result);
//            NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,parameters,result);
//        }else if ([URLString isEqualToString:PostLogin] || [URLString isEqualToString:PostBuyPower] || [URLString isEqualToString:PostSellPower] || [URLString isEqualToString:Postregister]|| [URLString isEqualToString:PostLogout]){
//            NSString * jsonStr = [self URLDecodedString:[[NSString alloc] initWithData:responseObject encoding:NSUTF8StringEncoding]];
//            NSString *resultStr = [RSA decryptString:jsonStr privateKey:APPRsaPrivateKey];
//            if (success) success(resultStr);
//            NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,parameters,resultStr);
//        }
        
        
    } failure:^(NSURLSessionDataTask * _Nullable task, NSError * _Nonnull error) {
        NSLog(@"\n response %@",task.originalRequest.allHTTPHeaderFields);
        NSLog(@"请求地址---->%@\n请求参数---->%@\n加密参数---->%@\n请求返回---->%@\n",URLString,parameters,parameters,error);
        if (error) {
//            NSHTTPURLResponse *response = (NSHTTPURLResponse *)task.response;
//            NSInteger httpStatus = response.statusCode;
            if (failure) failure(error.localizedDescription);
        }
    }];
}



#pragma mark -json串转换成数组
- (id)arrayWithJsonString:(NSString *)jsonString{
    
    if (jsonString == nil) {
        return nil;
    }
    
    NSData *jsonData = [jsonString dataUsingEncoding:NSUTF8StringEncoding];
    NSError *err;
    NSArray *arr = [NSJSONSerialization JSONObjectWithData:jsonData
                                                    options:NSJSONReadingMutableContainers
                                                    error:&err];
    
    if(err) {
        NSLog(@"json解析失败：%@",err);
        return nil;
    }
    return arr;
    
}


- (NSDictionary *)RSADictionary:(id)object {
    NSString *rsaPublicKey = UDValue(@"RsaPublicKey") ? UDValue(@"RsaPublicKey") : @"";
    if ([rsaPublicKey isEqual:@""]) {
        [SVProgressHUD showInfoWithStatus:@"请重新登录"];
        return nil;
    }
    NSString *jsonString = [self dataToJsonString:object];
    NSString *aesDncrypt = [RSAUtil encryptString:jsonString publicKey:rsaPublicKey];
    NSString *encodeUrl = [self urlEncodeUsingEncoding:aesDncrypt];
    NSString *md5String = [self MD5_32:jsonString];
    return @{@"encodeString":encodeUrl,
             @"sign" :md5String
    };
}
- (NSString*)dataToJsonString:(id)object{
    if ([object isKindOfClass:[NSString class]]) {
        return object;
    }
    NSString *jsonString = nil;
    NSError *error;
    NSData *jsonData = [NSJSONSerialization dataWithJSONObject:object
                                                       options:0 // Pass 0 if you don't care about the readability of the generated string
                                                         error:&error];
    if (! jsonData) {
        //        NSLog(@"Got an error: %@", error);
    } else {
        jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    }
    return jsonString;
}

- (NSString *)urlEncodeUsingEncoding:(NSString *)str {
    NSString *escapedString = [str stringByAddingPercentEncodingWithAllowedCharacters:[NSCharacterSet characterSetWithCharactersInString:@"#%<>[\\]^`{|}\"]+"].invertedSet];
        NSLog(@"escapedString: %@", escapedString);
    return escapedString;
}

/**
 *  URLDecode
 */
-(NSString *)URLDecodedString:(NSString *)urlStr{
    //NSString *decodedString = [encodedString stringByReplacingPercentEscapesUsingEncoding:NSUTF8StringEncoding ];
    
    NSString *encodedString = urlStr;
    NSString *decodedString  = (__bridge_transfer NSString *)CFURLCreateStringByReplacingPercentEscapesUsingEncoding(NULL,
                                                                                                                     (__bridge CFStringRef)encodedString,
                                                                                                                     CFSTR(""),
                                                                                                                     CFStringConvertNSStringEncodingToEncoding(NSUTF8StringEncoding));
    return decodedString;
}


- (NSString *)MD5_32:(NSString *)md5Str{
    if (md5Str.length < 1) {
        return nil;
    }
    
    const char *value = [md5Str UTF8String];
    
    unsigned char outputBuffer[CC_MD5_DIGEST_LENGTH];
    CC_MD5(value, (CC_LONG)strlen(value), outputBuffer);
    
    NSMutableString *outputString = [[NSMutableString alloc] initWithCapacity:CC_MD5_DIGEST_LENGTH * 2];
    for (NSInteger count = 0; count < CC_MD5_DIGEST_LENGTH; count++) {
        [outputString appendFormat:@"%02x",outputBuffer[count]];
    }
    
    return outputString;
}



#pragma mark ---公钥加密 && 私钥解密

//公钥加密
- (NSDictionary *)opensslPubcliKeyEncrypt:(id)object {
    
    NSString *rsaPublicKey = UDValue(@"RsaPublicKey") ? UDValue(@"RsaPublicKey") : @"";
    if ([rsaPublicKey isEqual:@""]) {
        [SVProgressHUD showInfoWithStatus:@"请重新登录"];
        return nil;
    }
    NSString *jsonString = [self dataToJsonString:object];
    
    NSData *plainData = [jsonString dataUsingEncoding:NSUTF8StringEncoding];
    RSA *publicKey = [DDRSAWrapper openssl_publicKeyFromBase64:rsaPublicKey];
    NSData *cipherData = [DDRSAWrapper openssl_encryptWithPublicKey:publicKey
                                                          plainData:plainData
                                                            padding:RSA_PKCS1_PADDING];

   NSString * cipherString = [cipherData base64EncodedStringWithOptions:NSDataBase64Encoding64CharacterLineLength];
    NSString *logText = [NSString stringWithFormat:@"openssl 公钥加密：\n%@",cipherString];
    NSLog(@"%@",logText);
    NSString *md5String = [self MD5_32:jsonString];
    return @{@"encodeString":cipherString,
             @"sign" :md5String
    };
    
//    [self opensslPrivateKeyDecrypt:cipherString];

}
//私钥解密
- (NSString *)opensslPrivateKeyDecrypt:(NSString *)cipherString{
    NSString *localPrivateKey = UDValue(@"localPrivateKey") ? UDValue(@"localPrivateKey") : @"";
    NSData *cipherData = [[NSData alloc] initWithBase64EncodedString:cipherString options:NSDataBase64DecodingIgnoreUnknownCharacters];

    RSA *privateKey = [DDRSAWrapper openssl_privateKeyFromBase64:localPrivateKey];
    
    NSData *plainData = [DDRSAWrapper openssl_decryptWithPrivateKey:privateKey
                                                         cipherData:cipherData
                                                            padding:RSA_PKCS1_PADDING];
    NSString *outputPlainString = [[NSString alloc] initWithData:plainData encoding:NSUTF8StringEncoding];
    return outputPlainString;
    
//    if ([outputPlainString isEqualToString:@"我是中国人123"]) {
//        NSString *logText = [NSString stringWithFormat:@"openssl 私钥解密：\n%@",outputPlainString];
//    } else {
//        NSString *logText = [NSString stringWithFormat:@"openssl 私钥解密失败"];
//    }
}

@end
