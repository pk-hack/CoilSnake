!define py2exeOutputDirectory 'dist'
!define exe 'CoilSnake.exe'

CRCCheck off
; Comment out the "SetCompress Off" line and uncomment
; the next line to enable compression. Startup times
; will be a little slower but the executable will be
; quite a bit smaller
SetCompress Off
;SetCompressor lzma

Name 'CoilSnake'
Caption 'CoilSnake'

OutFile ${exe}
RequestExecutionLevel user
SilentInstall normal
Icon 'coilsnake\assets\images\icon.ico'

Section
    SetAutoClose true

    InitPluginsDir
    SetOutPath '$PLUGINSDIR'
    File /r '${py2exeOutputDirectory}\*.*'

    GetTempFileName $0
    DetailPrint $0
    Delete $0
    StrCpy $0 '$0.bat'
    FileOpen $1 $0 'w'
    FileWrite $1 '@echo off$\r$\n'
    StrCpy $2 $TEMP 2
    FileWrite $1 '$2$\r$\n'
    FileWrite $1 'cd $PLUGINSDIR$\r$\n'
    FileWrite $1 '${exe}$\r$\n'
    FileClose $1
    HideWindow
    nsExec::Exec $0
    Delete $0
SectionEnd