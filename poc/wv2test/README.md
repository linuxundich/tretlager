# WebView2-Test unter Wine

Kleine C#-Programme, die WebView2 getrennt vom Zwift-Launcher prüfen (T2, 2026-10-29).
Gebaut mit dem `csc.exe` aus dem winetricks-.NET-4.8 im Prefix, gegen das NuGet-Paket
`Microsoft.Web.WebView2` 1.0.4314.35 (`lib/net462`, `runtimes/win-x64/native/WebView2Loader.dll`).

    F='C:\windows\Microsoft.NET\Framework64\v4.0.30319'
    wine "$F\csc.exe" /target:winexe /platform:x64 /out:WV2Test.exe \
      /r:Microsoft.Web.WebView2.Core.dll /r:Microsoft.Web.WebView2.WinForms.dll \
      /r:System.Windows.Forms.dll WV2Test.cs
    wine "$F\csc.exe" /target:winexe /platform:x64 /out:WV2Wpf.exe \
      /r:Microsoft.Web.WebView2.Core.dll /r:Microsoft.Web.WebView2.Wpf.dll \
      /r:"$F\WPF\PresentationFramework.dll" /r:"$F\WPF\PresentationCore.dll" \
      /r:"$F\WPF\WindowsBase.dll" /r:System.Xaml.dll WV2Wpf.cs

`WV2Wpf.exe hwnd` nutzt das klassische WPF-Steuerelement `WebView2`, `WV2Wpf.exe comp` das
`WebView2CompositionControl` des Launchers 1.2.
