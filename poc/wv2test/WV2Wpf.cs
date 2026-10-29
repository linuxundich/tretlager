using System; using System.IO; using System.Windows; using System.Windows.Threading;
using Microsoft.Web.WebView2.Core; using Microsoft.Web.WebView2.Wpf;
class P {
  static StreamWriter log;
  static void L(string s){ var l=DateTime.Now.ToString("HH:mm:ss.fff")+" "+s; Console.WriteLine(l); log.WriteLine(l); log.Flush(); }
  [STAThread] static void Main(string[] a){
    string mode = a.Length>0 ? a[0] : "hwnd";
    log=new StreamWriter("wv2wpf-"+mode+".log",false);
    var app=new Application();
    app.DispatcherUnhandledException+=(s,e)=>{ L("UNHANDLED "+e.Exception.GetType().Name+" 0x"+e.Exception.HResult.ToString("X8")+" "+e.Exception.Message); };
    AppDomain.CurrentDomain.UnhandledException+=(s,e)=>{ L("APPDOMAIN UNHANDLED "+e.ExceptionObject); };
    var win=new Window(){Title="WV2Wpf "+mode,Width=900,Height=700};
    IWebView2 wv = mode=="comp" ? (IWebView2)new WebView2CompositionControl() : (IWebView2)new WebView2();
    win.Content=(UIElement)wv;
    wv.CoreWebView2InitializationCompleted+=(s,e)=>{
      if(e.IsSuccess){ L("Init OK"); wv.CoreWebView2.Navigate("https://example.com/"); }
      else L("Init FAIL "+e.InitializationException.GetType().Name+" 0x"+e.InitializationException.HResult.ToString("X8")+" "+e.InitializationException.Message);
    };
    wv.NavigationCompleted+=(s,e)=>L("NavigationCompleted success="+e.IsSuccess+" title="+wv.CoreWebView2.DocumentTitle);
    win.Loaded+=async(s,e)=>{
      L("Loaded, mode="+mode);
      try { var env=await CoreWebView2Environment.CreateAsync(null, Path.Combine(Path.GetTempPath(),"wv2wpf-"+mode));
            L("Environment OK "+env.BrowserVersionString); await wv.EnsureCoreWebView2Async(env); L("EnsureCoreWebView2Async returned"); }
      catch(Exception ex){ L("EXC "+ex.GetType().Name+" 0x"+ex.HResult.ToString("X8")+" "+ex.Message); }
    };
    var t=new DispatcherTimer(){Interval=TimeSpan.FromSeconds(40)}; t.Tick+=(s,e)=>{L("timeout, exit"); app.Shutdown();}; t.Start();
    app.Run(win); L("end");
  }
}
