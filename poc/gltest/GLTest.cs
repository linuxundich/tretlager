// Prüft, ob Wine einen WGL-Kontext liefert, und gibt Hersteller, Renderer und Version aus.
// Gleicher Weg wie GLFW in ZwiftApp: Fenster, ChoosePixelFormat, wglCreateContext, glGetString.
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

class GLTest
{
    [StructLayout(LayoutKind.Sequential)]
    struct PIXELFORMATDESCRIPTOR
    {
        public ushort nSize, nVersion; public uint dwFlags; public byte iPixelType, cColorBits, cRedBits, cRedShift,
        cGreenBits, cGreenShift, cBlueBits, cBlueShift, cAlphaBits, cAlphaShift, cAccumBits, cAccumRedBits,
        cAccumGreenBits, cAccumBlueBits, cAccumAlphaBits, cDepthBits, cStencilBits, cAuxBuffers, iLayerType, bReserved;
        public uint dwLayerMask, dwVisibleMask, dwDamageMask;
    }
    [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr hwnd);
    [DllImport("gdi32.dll")] static extern int ChoosePixelFormat(IntPtr hdc, ref PIXELFORMATDESCRIPTOR pfd);
    [DllImport("gdi32.dll")] static extern bool SetPixelFormat(IntPtr hdc, int fmt, ref PIXELFORMATDESCRIPTOR pfd);
    [DllImport("opengl32.dll")] static extern IntPtr wglCreateContext(IntPtr hdc);
    [DllImport("opengl32.dll")] static extern bool wglMakeCurrent(IntPtr hdc, IntPtr ctx);
    [DllImport("opengl32.dll")] static extern IntPtr glGetString(uint name);

    static string S(uint n) { var p = glGetString(n); return p == IntPtr.Zero ? "(null)" : Marshal.PtrToStringAnsi(p); }

    static int Main()
    {
        var f = new Form { Width = 200, Height = 200, ShowInTaskbar = false };
        f.Show();
        IntPtr hdc = GetDC(f.Handle);
        var pfd = new PIXELFORMATDESCRIPTOR
        {
            nSize = (ushort)Marshal.SizeOf(typeof(PIXELFORMATDESCRIPTOR)), nVersion = 1,
            dwFlags = 0x4 | 0x20 | 0x1, // DRAW_TO_WINDOW | SUPPORT_OPENGL | DOUBLEBUFFER
            iPixelType = 0, cColorBits = 32, cDepthBits = 24, cStencilBits = 8
        };
        int fmt = ChoosePixelFormat(hdc, ref pfd);
        Console.WriteLine("ChoosePixelFormat: " + fmt);
        if (fmt == 0 || !SetPixelFormat(hdc, fmt, ref pfd)) { Console.WriteLine("FAIL: kein Pixelformat"); return 1; }
        IntPtr ctx = wglCreateContext(hdc);
        if (ctx == IntPtr.Zero || !wglMakeCurrent(hdc, ctx)) { Console.WriteLine("FAIL: kein Kontext"); return 1; }
        Console.WriteLine("GL_VENDOR:   " + S(0x1F00));
        Console.WriteLine("GL_RENDERER: " + S(0x1F01));
        Console.WriteLine("GL_VERSION:  " + S(0x1F02));
        return 0;
    }
}
