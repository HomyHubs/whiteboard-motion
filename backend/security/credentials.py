from __future__ import annotations
import ctypes,os
from ctypes import wintypes
from typing import Protocol

PREFIX='WhiteboardVideo'
def credential_target(provider_id:str)->str:return f'{PREFIX}/image-api/{provider_id}'

class CredentialStore(Protocol):
    def set(self,target:str,secret:str,username:str='api-key')->None:...
    def get(self,target:str)->str|None:...
    def delete(self,target:str)->bool:...

class InMemoryCredentialStore:
    def __init__(self):self.values={}
    def set(self,target:str,secret:str,username:str='api-key')->None:self.values[target]=secret
    def get(self,target:str)->str|None:return self.values.get(target)
    def delete(self,target:str)->bool:return self.values.pop(target,None) is not None

class WindowsCredentialStore:
    CRED_TYPE_GENERIC=1;CRED_PERSIST_LOCAL_MACHINE=2;ERROR_NOT_FOUND=1168
    class CREDENTIALW(ctypes.Structure):
        _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
    def __init__(self):
        if os.name!='nt':raise OSError('Windows Credential Manager is only available on Windows')
        self.advapi=ctypes.WinDLL('Advapi32.dll',use_last_error=True)
        self.advapi.CredWriteW.argtypes=[ctypes.POINTER(self.CREDENTIALW),wintypes.DWORD];self.advapi.CredWriteW.restype=wintypes.BOOL
        self.advapi.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(self.CREDENTIALW))];self.advapi.CredReadW.restype=wintypes.BOOL
        self.advapi.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD];self.advapi.CredDeleteW.restype=wintypes.BOOL
        self.advapi.CredFree.argtypes=[ctypes.c_void_p]
    def set(self,target:str,secret:str,username:str='api-key')->None:
        if not secret:raise ValueError('Secret cannot be empty')
        raw=secret.encode('utf-16-le');blob=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw);cred=self.CREDENTIALW()
        cred.Type=self.CRED_TYPE_GENERIC;cred.TargetName=target;cred.CredentialBlobSize=len(raw);cred.CredentialBlob=ctypes.cast(blob,ctypes.POINTER(ctypes.c_ubyte));cred.Persist=self.CRED_PERSIST_LOCAL_MACHINE;cred.UserName=username
        if not self.advapi.CredWriteW(ctypes.byref(cred),0):raise ctypes.WinError(ctypes.get_last_error())
    def get(self,target:str)->str|None:
        pointer=ctypes.POINTER(self.CREDENTIALW)()
        if not self.advapi.CredReadW(target,self.CRED_TYPE_GENERIC,0,ctypes.byref(pointer)):
            error=ctypes.get_last_error()
            if error==self.ERROR_NOT_FOUND:return None
            raise ctypes.WinError(error)
        try:
            cred=pointer.contents;raw=ctypes.string_at(cred.CredentialBlob,cred.CredentialBlobSize);return raw.decode('utf-16-le')
        finally:self.advapi.CredFree(pointer)
    def delete(self,target:str)->bool:
        if self.advapi.CredDeleteW(target,self.CRED_TYPE_GENERIC,0):return True
        error=ctypes.get_last_error()
        if error==self.ERROR_NOT_FOUND:return False
        raise ctypes.WinError(error)
