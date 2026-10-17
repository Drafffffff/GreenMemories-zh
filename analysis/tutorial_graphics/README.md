# Green Memories 图形汉化补丁

`tools/tutorial_graphics_zh.py` 提供 `apply_graphics(rom: bytearray) -> dict`，`apply_tutorials` 为兼容别名。完整构建由主 `tools/build_zh.py` 负责；本模块不改原 ROM 文件。

## 已处理资源

共 88 个 Butano regular_bg_item：82 张 32×32 tile 方图，加 4 张 32×160 tile 分类长图和 2 张 192×32 tile 菜单顶栏图集。英文与葡文图形分支均使用中文画面；完整汉化动态文本以第一个语言入口为准。

覆盖天气和武器教程 8 页、操作图、状态/饰品/金币、物品/装备、任务、地图及未知区域、系统/存档/操作说明/返回标题、存入/取出原料、制作、购买/出售、死亡画面、未完待续、制作名单角色。六个旧版实际菜单顶栏与五类物品侧栏包含在长图集中。原始作者名、游戏品牌与通用 HP/ST 缩写保留。教程图示、页码、导航点、按键图标和菜单 L/R 原图标保留。

## 技术证据和验证

原 ROM SHA-256：`a5bf6ba5d6f78912e35986ba21cf034c65677cc66c3f97022606069dbaafb202`。

这些资源是原始 4bpp 图块与 16-bit tilemap，未经 LZ 压缩。描述符前两字段为图块 span，+24 为地图指针；+8…+23 的色板/压缩字段和 +28…+39 的地图尺寸/标记均保持原值。图块按水平/垂直镜像去重。79 个资源在原区内写回，9 个资源因图块数量略增而附加到 ROM，只修改对应描述符的显式 span/map 指针。

每次构建会对最终 ROM 的 88 个资源全部重新解码，与预期像素 SHA-256 比较，并断言色板/尺寸/标记未变。详见 `patch_report.json`。最长资源并非压缩 OBJ：实际菜单顶栏从 BG3 显示，ROM 描述符 `0x8272a8/0x8272d0`；分类侧栏从四个 32×160 图集显示。

`graphics_probe.gba` 是原版加本模块图片补丁的独立开发验证 ROM，不是最终完整汉化输出。`check.py` 在 mGBA core 中验证八页教程、关闭教程/按键说明、进入实际场景、状态页与六个菜单切页；`zh_runtime_*` 为截图。纯图验证 ROM 的动态剧情和 Exit/Confirm 仍为原文，完整构建会由文本引擎替换，不能把纯图验证 ROM 作为最终版本交付。最新完整 ROM 的动态提示由主构建者检查。

## 字体与复现依赖

教程正文和实际旧菜单顶栏使用 Fusion Pixel 12px；紧凑菜单标签使用 10px、8px，按钮提示保留原紧凑高度。字体 BDF、OFL 授权和来源说明均在 `assets/tutorial_graphics/fonts/`，无需其他游戏目录。模块另需本目录 `inventory.json`（82 个原资源的地址清单），Python 3 与 Pillow。

本验证未覆盖完整通关或实机；其他动态图文与世界场景由主汉化模块负责。

额外原版对照：`original_item_consumable_3x.png` 与 `original_item_up_3x.png`。原版进入物品栏先显示空 CONSUM.，按 Up 后 WEAPONS 原本即列出 Bottle、Pistol、Machete 三项；中文版“武器”下出现水壶属于原游戏已有分组行为，分类图集未发生顺序反转。四张原图集从上到下均为 CONSUM. / RESOURCES / KEY ITEMS / ACCESSORIES / WEAPONS。
