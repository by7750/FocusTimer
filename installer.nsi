
                !include "MUI2.nsh"
                
                ; 应用程序信息
                Name "专注学习计时器"
                OutFile "专注学习计时器安装程序.exe"
                
                ; 默认安装目录
                InstallDir "$PROGRAMFILES\专注学习计时器"
                
                ; 请求应用程序权限
                RequestExecutionLevel admin
                
                ; 界面设置
                !define MUI_ABORTWARNING
                !define MUI_ICON "resources\icons\icon.png"
                
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
                    File /r "dist\专注学习计时器\*.*"
                    
                    ; 创建开始菜单快捷方式
                    CreateDirectory "$SMPROGRAMS\专注学习计时器"
                    CreateShortcut "$SMPROGRAMS\专注学习计时器\专注学习计时器.lnk" "$INSTDIR\专注学习计时器.exe"
                    CreateShortcut "$SMPROGRAMS\专注学习计时器\卸载.lnk" "$INSTDIR\卸载.exe"
                    
                    ; 创建桌面快捷方式
                    CreateShortcut "$DESKTOP\专注学习计时器.lnk" "$INSTDIR\专注学习计时器.exe"
                    
                    ; 创建卸载程序
                    WriteUninstaller "$INSTDIR\卸载.exe"
                    
                    ; 添加卸载信息到控制面板
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\专注学习计时器" "DisplayName" "专注学习计时器"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\专注学习计时器" "UninstallString" "$INSTDIR\卸载.exe"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\专注学习计时器" "DisplayIcon" "$INSTDIR\专注学习计时器.exe"
                    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\专注学习计时器" "Publisher" "FocusTimer"
                SectionEnd
                
                ; 卸载部分
                Section "Uninstall"
                    ; 删除程序文件
                    RMDir /r "$INSTDIR"
                    
                    ; 删除开始菜单快捷方式
                    RMDir /r "$SMPROGRAMS\专注学习计时器"
                    
                    ; 删除桌面快捷方式
                    Delete "$DESKTOP\专注学习计时器.lnk"
                    
                    ; 删除注册表项
                    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\专注学习计时器"
                SectionEnd
                