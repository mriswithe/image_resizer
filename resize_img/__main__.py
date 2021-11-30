# First things, first. Import the wxPython package.
import wx
from . import main


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pnl = wx.Panel(self)
        button = wx.Button(pnl, label="Do Stuff")
        font = button.GetFont()
        font.PointSize += 10
        font = font.Bold()
        button.SetFont(font)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(button, wx.SizerFlags().Border(wx.TOP | wx.LEFT, 25))
        pnl.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self.button_pressed, button)

    def button_pressed(self, event):
        resp = main()
        wx.MessageBox(resp)


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(name)s [%(levelname)s]:%(message)s"
    )
    # Start the event loop.
    app = wx.App()
    frame = MainFrame(None, title="Image resizer")
    frame.Show()
    app.MainLoop()
