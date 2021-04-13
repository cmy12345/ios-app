
# RSA
In this folder, we have files to generate RSA public key pairs using Openssl and ios native. The files DDRSAWrapper+openssl.m and DDRSAWrapper+openssl.h is randomly generating key pairs on iOS.

The files RSAUtil.h and RSAUtil.m is the encrypt and decrypt part. The key string is too long we need to separate and encrypt and decrypt each part. In our project we use DDRSAWrapper+openssl.m and DDRSAWrapper+openssl.h as the method we use to generate our RSA key pairs
