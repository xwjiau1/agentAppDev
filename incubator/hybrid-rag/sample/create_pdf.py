"""Regenerate the small text PDF fixture with ReportLab 5.1.0."""
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


def main():
    target = Path(__file__).parent / "corpus" / "policies" / "refund.pdf"
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    document = canvas.Canvas(str(target), invariant=True)
    document.setTitle("Refund policy fixture")
    for lines in (
        ("退款申请应在付款后十四天内提交。", "审核进度可在订单管理页面查看。"),
        ("审批通过后，退款将在五个工作日内原路退回。", "审核进度可在订单管理页面查看。"),
    ):
        document.setFont("STSong-Light", 14)
        for index, line in enumerate(lines):
            document.drawString(50, 760 - index * 24, line)
        document.showPage()
    document.save()


if __name__ == "__main__":
    main()
