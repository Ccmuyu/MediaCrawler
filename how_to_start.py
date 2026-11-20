"""打印本项目的启动方法。运行：python how_to_start.py"""


def main() -> None:
    print(
        """
MediaCrawler 启动方法
先完成一次安装，之后用 WebUI 或命令行都可以。

【安装】在项目根目录执行
  uv sync

【方式一：WebUI】
  1. 启动页面
       cd webui
       pnpm install
       pnpm dev
  2. 浏览器打开 http://localhost:5173
  3. 打开页面顶栏的「后端 API」开关，等到状态变成「已启动」

  也可以在项目根目录另开一个终端，手动启动 API：
       uv run uvicorn api.main:app --port 8080 --reload

【方式二：命令行】在项目根目录执行
  查看全部参数
       uv run main.py --help

  按关键词搜索（浏览器扫码登录）
       uv run main.py --platform xhs --lt qrcode --type search

  抓取指定帖子
       uv run main.py --platform xhs --lt qrcode --type detail --specified_id <帖子URL或ID>

  抓取创作者主页
       uv run main.py --platform dy --lt qrcode --type creator --creator_id <主页URL或ID>

结果写在项目根目录的 data/ 下。
""".strip()
    )


if __name__ == "__main__":
    main()
