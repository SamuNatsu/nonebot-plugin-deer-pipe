<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://raw.githubusercontent.com/SamuNatsu/nonebot-plugin-deer-pipe/main/assets/deerpipe.jpg" width="220" height="180" alt="Logo"></a>
</div>

<div align="center">

# nonebot-plugin-deer-pipe

_✨ 每月🦌管签到 ✨_

<a href="./LICENSE"><img src="https://img.shields.io/github/license/SamuNatsu/nonebot-plugin-deer-pipe.svg" alt="license"></a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-deer-pipe"><img src="https://img.shields.io/pypi/v/nonebot-plugin-deer-pipe.svg" alt="pypi"></a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">

</div>

## 📖 介绍

一个🦌管签到小插件

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-deer-pipe

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令
<details>
<summary>pip</summary>

    pip install nonebot-plugin-deer-pipe

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-deer-pipe

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-deer-pipe

</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-deer-pipe

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_deer_pipe"]

</details>

## ⚙️ 配置

该插件使用了 `nonebot-plugin-localstore` 来决定用户数据的存放位置，你可能需要对其进行配置

## 🎉 使用
### 指令表

发送一个 `🦌` 即可触发签到  
发送命令 `补🦌 <日期>` 以进行补签，如：`补🦌 1`（补签本月 1 日）

签到每月自动刷新
