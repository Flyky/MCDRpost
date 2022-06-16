# MCDRpost

A MCDR plugin for post/teleport items  
一个用于邮寄/传送物品的MCDR插件  

[-> MCDReforged <-](https://github.com/Fallen-Breath/MCDReforged)

![MCDRpost help](https://s1.ax1x.com/2020/04/16/Jk8ysP.png)

# Install

将`MCDRpost.mcdr`放入plugins目录下重载插件即可  
**当前必须使用Rcon获取信息，请一定配置好服务器和MCDR的Rcon**  
*MCDRpost(ver1.0.0+)依赖[Minecraft Data API插件](https://github.com/MCDReforged/MinecraftDataAPI)，请先安装[Minecraft Data API插件](https://github.com/MCDReforged/MinecraftDataAPI)*  
*旧版本依赖[PlayerInfoAPI插件](https://github.com/TISUnion/PlayerInfoAPI)*  
# Feature

**使用该插件可以将副手的物品发送给别的玩家**  
也可以发送给离线玩家（但该玩家必须曾经进过服务器）  
*不可以发送给自己哦~*  

- 玩家发出物品后，物品(订单)将会存放在【中转站】
- 需要收件人收取订单才能收到物品，之后【中转站】会删除该订单
- 还未查收的订单可以取消，物品会从【中转站】退回，并删除订单
- 每人存放【中转站】的订单数有上限（防止作为储存箱等的滥用），默认为 5  
- 如果你要问为啥一定是副手用replaceitem传送接收呢 ，因为
    - 用give传到身上任意栏位，如果身上东西多的话，传回来还要找一下，比较麻烦，还不容易找到传回来的是哪个东西
    - 如果身上东西满了的话give是拿不到物品的，防止粗心大意的小天才
    - 该插件传送和接收前均会检查并提示副手物品，不用担心会直接replace掉原本副手的物品
    - 当然为什么不传送当前主手所持栏位进行传送呢？ 因为我懒2333
    - minecraft ver1.17之后移除了`replaceitem`命令，改为了`item replace`

## Usage

- `!!po` 显示帮助信息
- `!!po p [收件人id] [备注]` 将副手物品发送给[收件人]，[备注]为可选项
- `!!po rl` 列出收件列表。包括[发件人]，[寄件时间]，[备注消息]和[单号]
- `!!po r [单号]` 确认收取该单号的物品到副手(收取前将副手清空)
- `!!po pl` 列出发件(待收取)列表，包括[收件人]，[寄件时间]，[备注消息]和[单号]
- `!!po c [单号]` 取消传送物品(收件人还未收件前)，该单号物品退回到副手(取消前将副手清空)
- `!!po ls players` 查看可被寄送的注册玩家列表 
- `!!po ls orders` 查看当前中转站内所有订单 [helper以上权限可用]
- `!!po player add [玩家id]` 手动注册玩家到可寄送玩家列表 [admin以上权限可用]
- `!!po player remove [玩家id]` 删除某注册的玩家 [admin以上权限可用]
  
*上面命令中的`r`表示`receive`，`p`表示`post`，`l`表示`list`，`c`表示`cancel`*  

## ATTENTIONS!!

- 可能会有部分带有特殊复杂NBT标签的物品无法传送，会提示检测不到可传送的物品，所以尝试一下即可
- **切勿传送原版非法堆叠数的物品**，例如使用carpet地毯堆叠的空潜影盒，会导致该物品无法接收
  
## known issues
~~因引用的`PlayerInfoAPI插件`在查询不到数据时的默认响应时间timeout较长，即在收寄时的检测副手为空的响应时间较长  ~~
~~所以在收寄过程时可能需要稍作等待~~
**~~但服务器开启并设置好MCDR可连接的rcon则不会出现此问题~~**~~，所以墙裂建议配置rcon~~  
**必须使用Rcon获取信息，请一定配置好服务器和MCDR的Rcon**

# pics

![po rl](https://s1.ax1x.com/2020/04/16/Jk0WnJ.png)  
![po r](https://s1.ax1x.com/2020/04/16/Jk0fB9.png)  
![po p](https://s1.ax1x.com/2020/04/16/Jk02X4.png)  
