Java.perform(function () {
    console.log("Starting Certificate Pinning Bypass for checkServerTrusted");

    try {
        // Hooking into X.0Et
        // How to find class:
        // Search for '.super Ljavax/net/ssl/X509ExtendedTrustManager;' in decoded apk
        let class_name = 'X.0F1';
        var EtClass = Java.use(class_name);
        console.log(`Found class: ${class_name}`);

        EtClass.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function (certs, authType) {
            console.log(`Bypassing checkServerTrusted in ${class_name} with String`);
            return;
        };

        EtClass.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'java.net.Socket').implementation = function (certs, authType, socket) {
            console.log(`Bypassing checkServerTrusted in ${class_name} with Socket`);
            return;
        };

        EtClass.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'javax.net.ssl.SSLEngine').implementation = function (certs, authType, sslEngine) {
            console.log(`Bypassing checkServerTrusted in ${class_name} with SSLEngine`);
            return;
        };

        // Hooking into X.0AM
        // How to find class:
        // Search for '.implements Ljavax/net/ssl/X509TrustManager;' 
        // Then check which has an annotation with value '"Ljava/util/Set<", "Ljava/nio/ByteBuffer;",' in instance fields in code
        let class_name2 = 'X.0Ax';
        var AMClass = Java.use(class_name2);
        console.log(`Found class: ${class_name2}`);

        AMClass.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function (certs, authType) {
            console.log(`Bypassing checkServerTrusted in ${class_name2} with String`);
            return;
        };
        
    } catch (err) {
        console.log("Error hooking into SSL methods: " + err);
    }
    console.log('SSL Pinning Bypass done');
    
});



