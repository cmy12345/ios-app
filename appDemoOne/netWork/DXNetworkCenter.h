//
//  DXNetworkCenter.h
//  UserRetention
//
//  Created by wendf on 2020/4/21.
//  Copyright © 2020 ChinaTelecom. All rights reserved.
//

#import "AFHTTPSessionManager.h"


@interface DXNetworkCenter : AFHTTPSessionManager

+ (instancetype)managerDXNetwork;


//- (NSURLSessionDataTask *)GET:(NSString *)URLString
//                   parameters:(id)parameters
//                      success:(void (^)(id responseObject))success
//                      failure:(void (^)(id responseObject, NSError *error))failure;

- (NSURLSessionDataTask *)POST:(NSString *)URLString
                    parameters:(id)parameters
                       success:(void (^)(id responseObject))success
                       failure:(void (^)(id  responseObject))failure;
- (NSURLSessionDataTask *)newPOST:(NSString *)URLString
                    parameters:(id)parameters
                       success:(void (^)(id responseObject))success
                          failure:(void (^)(id responseObject))failure;

@end

