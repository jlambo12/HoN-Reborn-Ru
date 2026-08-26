using System.Drawing.Drawing2D;

namespace HoNRebornRu.Launcher;

internal static class LauncherTheme
{
    public static readonly Color Background = Color.FromArgb(8, 11, 14);
    public static readonly Color Card = Color.FromArgb(232, 13, 18, 23);
    public static readonly Color CardRaised = Color.FromArgb(242, 17, 24, 32);
    public static readonly Color Border = Color.FromArgb(37, 48, 58);
    public static readonly Color BorderHover = Color.FromArgb(88, 72, 68);
    public static readonly Color Text = Color.FromArgb(232, 233, 234);
    public static readonly Color Muted = Color.FromArgb(143, 154, 165);
    public static readonly Color Red = Color.FromArgb(181, 39, 36);
    public static readonly Color BrightRed = Color.FromArgb(222, 59, 50);
    public static readonly Color Burgundy = Color.FromArgb(114, 29, 26);
    public static readonly Color Gold = Color.FromArgb(208, 163, 73);
    public static readonly Color Warning = Color.FromArgb(216, 165, 58);
    public static readonly Color Success = Color.FromArgb(94, 168, 107);
    public static readonly Color Error = Color.FromArgb(207, 75, 68);

    public static GraphicsPath Rounded(Rectangle bounds, int radius)
    {
        var path = new GraphicsPath();
        if (bounds.Width <= 0 || bounds.Height <= 0) return path;
        var diameter = Math.Min(Math.Min(bounds.Width, bounds.Height), Math.Max(2, radius * 2));
        var arc = new Rectangle(bounds.X, bounds.Y, diameter, diameter);
        path.AddArc(arc, 180, 90);
        arc.X = bounds.Right - diameter;
        path.AddArc(arc, 270, 90);
        arc.Y = bounds.Bottom - diameter;
        path.AddArc(arc, 0, 90);
        arc.X = bounds.X;
        path.AddArc(arc, 90, 90);
        path.CloseFigure();
        return path;
    }

    public static Color Blend(Color from, Color to, float amount) => Color.FromArgb(
        (int)(from.A + (to.A - from.A) * amount),
        (int)(from.R + (to.R - from.R) * amount),
        (int)(from.G + (to.G - from.G) * amount),
        (int)(from.B + (to.B - from.B) * amount));
}

internal sealed class LauncherCard : Panel
{
    public int CornerRadius { get; set; } = 10;
    public Color FillColor { get; set; } = LauncherTheme.Card;
    public Color BorderColor { get; set; } = LauncherTheme.Border;

    public LauncherCard()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
                 ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
        BackColor = Color.Transparent;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        if (Width <= 1 || Height <= 1) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var bounds = new Rectangle(0, 0, Width - 1, Height - 1);
        using var path = LauncherTheme.Rounded(bounds, CornerRadius);
        using var fill = new SolidBrush(FillColor);
        using var border = new Pen(BorderColor);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(border, path);
    }
}

internal enum LauncherButtonKind
{
    Primary,
    Secondary,
    Ghost,
    Danger
}

internal sealed class LauncherButton : Button
{
    private readonly System.Windows.Forms.Timer _animation;
    private float _hoverAmount;
    private bool _hovered;
    private bool _pressed;

    public LauncherButtonKind Kind { get; set; } = LauncherButtonKind.Secondary;
    public int CornerRadius { get; set; } = 7;

    public LauncherButton()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
                 ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        FlatStyle = FlatStyle.Flat;
        FlatAppearance.BorderSize = 0;
        UseVisualStyleBackColor = false;
        Cursor = Cursors.Hand;
        Font = new Font("Segoe UI Semibold", 9, FontStyle.Bold);
        ForeColor = LauncherTheme.Text;
        _animation = new System.Windows.Forms.Timer { Interval = 16 };
        _animation.Tick += (_, _) => AnimateHover();
    }

    protected override void OnMouseEnter(EventArgs e) { _hovered = true; _animation.Start(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { _hovered = false; _pressed = false; _animation.Start(); base.OnMouseLeave(e); }
    protected override void OnMouseDown(MouseEventArgs e) { if (e.Button == MouseButtons.Left) _pressed = true; Invalidate(); base.OnMouseDown(e); }
    protected override void OnMouseUp(MouseEventArgs e) { _pressed = false; Invalidate(); base.OnMouseUp(e); }
    protected override void OnEnabledChanged(EventArgs e) { Invalidate(); base.OnEnabledChanged(e); }

    private void AnimateHover()
    {
        var target = _hovered ? 1f : 0f;
        _hoverAmount += (target - _hoverAmount) * .28f;
        if (Math.Abs(target - _hoverAmount) < .02f)
        {
            _hoverAmount = target;
            _animation.Stop();
        }
        Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        if (Width <= 3 || Height <= 3) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var bounds = new Rectangle(1, 1 + (_pressed ? 1 : 0), Width - 3, Height - 3);
        using var path = LauncherTheme.Rounded(bounds, CornerRadius);

        var (baseColor, hoverColor, borderColor) = Kind switch
        {
            LauncherButtonKind.Primary => (LauncherTheme.Burgundy, LauncherTheme.Red, LauncherTheme.Gold),
            LauncherButtonKind.Danger => (Color.FromArgb(66, 28, 28), Color.FromArgb(99, 35, 33), LauncherTheme.Error),
            LauncherButtonKind.Ghost => (Color.FromArgb(8, 13, 17), Color.FromArgb(27, 34, 40), LauncherTheme.Border),
            _ => (Color.FromArgb(31, 40, 48), Color.FromArgb(43, 54, 63), LauncherTheme.BorderHover)
        };

        if (!Enabled)
        {
            baseColor = Color.FromArgb(28, 31, 34);
            hoverColor = baseColor;
            borderColor = Color.FromArgb(47, 51, 54);
        }

        var top = LauncherTheme.Blend(baseColor, hoverColor, _hoverAmount);
        var bottom = LauncherTheme.Blend(Color.FromArgb(baseColor.A, Math.Max(0, baseColor.R - 20), Math.Max(0, baseColor.G - 12), Math.Max(0, baseColor.B - 10)), hoverColor, _hoverAmount * .55f);
        if (Kind == LauncherButtonKind.Primary && Enabled)
        {
            using var glow = new Pen(Color.FromArgb((int)(35 + 55 * _hoverAmount), LauncherTheme.BrightRed), 3);
            e.Graphics.DrawPath(glow, path);
        }
        using var fill = new LinearGradientBrush(bounds, top, bottom, LinearGradientMode.Vertical);
        using var border = new Pen(borderColor);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(border, path);

        var color = Enabled ? ForeColor : Color.FromArgb(105, 110, 114);
        TextRenderer.DrawText(e.Graphics, Text, Font, bounds, color,
            TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) _animation.Dispose();
        base.Dispose(disposing);
    }
}

internal sealed class LauncherRadioCard : Control
{
    private bool _selected;
    private bool _hovered;

    public string Title { get; set; } = "";
    public string Subtitle { get; set; } = "";
    public bool Selected
    {
        get => _selected;
        set { _selected = value; Invalidate(); }
    }

    public LauncherRadioCard()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
                 ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        Cursor = Cursors.Hand;
        TabStop = true;
    }

    protected override void OnMouseEnter(EventArgs e) { _hovered = true; Invalidate(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { _hovered = false; Invalidate(); base.OnMouseLeave(e); }
    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (e.KeyCode is Keys.Space or Keys.Enter) { OnClick(EventArgs.Empty); e.Handled = true; }
        base.OnKeyDown(e);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        if (Width <= 1 || Height <= 1) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var bounds = new Rectangle(0, 0, Width - 1, Height - 1);
        using var path = LauncherTheme.Rounded(bounds, 8);
        var fillColor = Selected ? Color.FromArgb(238, 35, 25, 27) : _hovered ? Color.FromArgb(241, 24, 31, 38) : LauncherTheme.CardRaised;
        var lineColor = Selected ? LauncherTheme.Red : _hovered ? LauncherTheme.BorderHover : LauncherTheme.Border;
        using var fill = new SolidBrush(fillColor);
        using var border = new Pen(lineColor, Selected ? 1.5f : 1f);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(border, path);

        var radio = new Rectangle(15, 18, 16, 16);
        using var radioBorder = new Pen(Selected ? LauncherTheme.Gold : LauncherTheme.Muted, 1.5f);
        e.Graphics.DrawEllipse(radioBorder, radio);
        if (Selected)
        {
            using var dot = new SolidBrush(LauncherTheme.BrightRed);
            e.Graphics.FillEllipse(dot, new Rectangle(19, 22, 8, 8));
        }

        using var titleFont = new Font("Segoe UI Semibold", 9.5f, FontStyle.Bold);
        using var subtitleFont = new Font("Segoe UI", 8.2f);
        TextRenderer.DrawText(e.Graphics, Title, titleFont, new Rectangle(42, 11, Width - 52, 23), LauncherTheme.Text,
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
        TextRenderer.DrawText(e.Graphics, Subtitle, subtitleFont, new Rectangle(42, 34, Width - 52, 22), LauncherTheme.Muted,
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
    }
}

internal sealed class LauncherProgressBar : Control
{
    private int _value;
    public int Value
    {
        get => _value;
        set { _value = Math.Clamp(value, 0, 100); Invalidate(); }
    }

    public LauncherProgressBar()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
                 ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        Height = 14;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        if (Width <= 1 || Height <= 1) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var bounds = new Rectangle(0, 0, Width - 1, Height - 1);
        using var track = LauncherTheme.Rounded(bounds, Height / 2);
        using var trackFill = new SolidBrush(Color.FromArgb(31, 38, 44));
        e.Graphics.FillPath(trackFill, track);
        if (Value <= 0) return;
        var fillWidth = Math.Max(Height, (int)(bounds.Width * Value / 100f));
        var fillBounds = new Rectangle(0, 0, Math.Min(bounds.Width, fillWidth), bounds.Height);
        using var fillPath = LauncherTheme.Rounded(fillBounds, Height / 2);
        using var fill = new LinearGradientBrush(fillBounds, LauncherTheme.BrightRed, LauncherTheme.Burgundy, LinearGradientMode.Horizontal);
        e.Graphics.FillPath(fill, fillPath);
    }
}

internal static class LauncherDialog
{
    public static bool Confirm(IWin32Window owner, string title, string message, string confirmText)
    {
        using var form = new Form
        {
            Text = title,
            ClientSize = new Size(460, 220),
            FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent,
            MaximizeBox = false,
            MinimizeBox = false,
            ShowInTaskbar = false,
            BackColor = LauncherTheme.Background,
            ForeColor = LauncherTheme.Text,
            AutoScaleMode = AutoScaleMode.Dpi
        };
        var heading = new Label
        {
            Text = title, Location = new Point(28, 24), Size = new Size(404, 28),
            Font = new Font("Segoe UI Semibold", 13, FontStyle.Bold), ForeColor = LauncherTheme.Gold
        };
        var body = new Label
        {
            Text = message, Location = new Point(28, 65), Size = new Size(404, 70),
            Font = new Font("Segoe UI", 9.5f), ForeColor = LauncherTheme.Text
        };
        var confirm = new LauncherButton
        {
            Text = confirmText, Kind = LauncherButtonKind.Primary,
            Location = new Point(212, 158), Size = new Size(220, 40), DialogResult = DialogResult.OK
        };
        var cancel = new LauncherButton
        {
            Text = "ОТМЕНА", Kind = LauncherButtonKind.Ghost,
            Location = new Point(28, 158), Size = new Size(168, 40), DialogResult = DialogResult.Cancel
        };
        form.Controls.AddRange([heading, body, confirm, cancel]);
        form.AcceptButton = confirm;
        form.CancelButton = cancel;
        return form.ShowDialog(owner) == DialogResult.OK;
    }
}
