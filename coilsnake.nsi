!define cxfreezeOutputDirectory 'build/exe.win-amd64-3.6'
!define exe 'CoilSnake.exe'

CRCCheck on
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
Icon 'coilsnake\assets\images\icon.ico'

SilentInstall normal
AutoCloseWindow true
ShowInstDetails nevershow

AddBrandingImage top 164 5
PageEx InstFiles
    Caption ": Loading"
PageExEnd

Section
    InitPluginsDir
    SetOutPath '$PLUGINSDIR'

    File "${cxfreezeOutputDirectory}\coilsnake\assets\images\splash.bmp"
    SetBrandingImage /RESIZETOFIT $PLUGINSDIR\splash.bmp
    DetailPrint "Loading CoilSnake..."
    SetDetailsPrint none

    File /r '${cxfreezeOutputDirectory}\*.*'

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