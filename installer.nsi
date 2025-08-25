
                !include "MUI2.nsh"
                
                ; 应用程序信息
                Name "FocusTimer"
                OutFile "FocusTimer-Setup.exe"
                
                ; 默认安装目录
                InstallDir "$PROGRAMFILES\FocusTimer"
                
                ; 请求应用程序权限
                RequestExecutionLevel admin
                
                ; 界面设置
                !define MUI_ABORTWARNING
                !define MUI_ICON "resources\icons\app_icon.ico"
                
                ; 页面
                !insertmacro MUI_PAGE_WELCOME
                !insertmacro MUI_PAGE_DIRECTORY
                !insertmacro MUI_PAGE_INSTFILES
                !insertmacro MUI_PAGE_FINISH
                
                ; 语言
                !insertmacro MUI_LANGUAGE "SimpChinese"
                
                ; 安装部分
                Section "安装程序文件" SecMain
                    SetOutPath "$INSTDIR"
                    
                    ; 复制所有文件
                    File /r "dist\FocusTimer\*.*"
                    
                    ; 明确复制资源文件（确保图标等资源被包含）
                    SetOutPath "$INSTDIR\resources\icons"
                    File "resources\icons\app_icon.ico"
                    File "resources\icons\icon.png"
                    File "resources\icons\music_pause.png"
                    File "resources\icons\music_play.png"
                    File "resources\icons\music_stop.png"
                    File "resources\icons\timer_change.png"
                    File "resources\icons\timer_pause.png"
                    File "resources\icons\timer_reset.png"
                    File "resources\icons\timer_start.png"
                    File "resources\icons\timer_stop.png"
                    
                    SetOutPath "$INSTDIR\resources\sounds"
                    ; 如果有声音文件也在这里添加
                    
                    SetOutPath "$INSTDIR\resources\styles"
                    ; 如果有样式文件也在这里添加
                    
                    ; 创建开始菜单快捷方式
                    CreateDirectory "$SMPROGRAMS\FocusTimer"
                    CreateShortcut "$SMPROGRAMS\FocusTimer\FocusTimer.lnk" "$INSTDIR\FocusTimer.exe"
                    CreateShortcut "$SMPROGRAMS\FocusTimer\卸载.lnk" "$INSTDIR\卸载.exe"
                    
                    ; 创建桌面快捷方式
                    CreateShortcut "$DESKTOP\FocusTimer.lnk" "$INSTDIR\FocusTimer.exe"
                    
                    ; 创建卸载程序
                    WriteUninstaller "$INSTDIR\卸载.exe"
                    
                    ; 添加卸载信息到控制面板
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FocusTimer" "DisplayName" "FocusTimer"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FocusTimer" "UninstallString" "$INSTDIR\卸载.exe"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FocusTimer" "DisplayIcon" "$INSTDIR\FocusTimer.exe"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FocusTimer" "Publisher" "FocusTimer"
                SectionEnd
                
                ; 卸载部分
                Section "Uninstall"
                    ; 删除程序文件
                    RMDir /r "$INSTDIR"
                    
                    ; 删除开始菜单快捷方式
                    RMDir /r "$SMPROGRAMS\FocusTimer"
                    
                    ; 删除桌面快捷方式
                    Delete "$DESKTOP\FocusTimer.lnk"
                    
                    ; 删除注册表项
                    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FocusTimer"
                SectionEnd
                