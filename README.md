# MCDRpost
A MCDR plugin for post/teleport items  
一个用于邮寄/传送物品的MCDR插件

# install
将MCDRpost.py放入plugins目录下重载插件即可
*MCDRpost依赖PlayerInfoAPI插件，请先安装PlayerInfoAPI插件*
   
# Feature
**使用该插件可以将副手的物品发送给别的玩家**  
## usage
- `!!po` 显示帮助信息
- `!!po p [收件人id] [备注]` 将副手物品发送给[收件人]，[备注]为可选项
- `!!po rl` 列出收件列表。包括[发件人]，[寄件时间]，[备注消息]和[单号]
- `!!po r [单号]` 确认收取该单号的物品到副手(收取前将副手清空)
- `!!po pl` 列出发件(待收取)列表，包括[收件人]，[寄件时间]，[备注消息]和[单号]
- `!!po c [单号]` 取消传送物品(收件人还未收件前)，该单号物品退回到副手(取消前将副手清空)
  
*上面命令中的`r`表示`receive`，`p`表示`post`，`l`表示`list`，`c`表示`cancel`*