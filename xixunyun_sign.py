from usr_record import Xixunyun_record
import json
from datetime import datetime, timedelta
import re
import chinese_calendar
import random
import rsa
import base64
from usr_qian import Xixunyun_qian
import asyncio
#from loglog import XXYLogger
import time
import os
##################################################
##logger.inf = XXYLogger('task', log_file='task.log')
weizhi = os.path.dirname(os.path.abspath(__file__))
##################导入配置文件#####################
try:
    with open(f'{weizhi}{os.sep}data{os.sep}config.json', 'r',encoding="utf-8") as file:
        data = json.load(file)
        config = data['config'][0]
        version_config = config['version']
        from_config = config['from']
        platform_config = config['platform']
        key_config = r"{}".format(config['key'])
except:
    print("配置文件错误，结束运行 | 配置文件：config.json")
    os._exit()
# 加载通知服务
def load_send():
    import sys
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/sendNotify.py"):
        try:
            from sendNotify import send
            return send
        except Exception as e:
            #print(f"加载通知服务失败：{e}")
            return None
    else:
        print("加载通知服务失败")
        return None
###########################################

def ageing(moth):
    if not re.match(r'^\d{4}-\d{2}:\d{4}-\d{2}$', moth):
        #logger.inf.info("用户的时间范围格式不正确，应为'年-月:年-月'。")
        print("用户的时间范围格式不正确，应为'年-月:年-月'。")
        return False
    start_date, end_date = moth.split(':')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m')
        end_date = datetime.strptime(end_date, '%Y-%m')
    except ValueError:
        #logger.inf.info("用户时间范围中的日期部分格式不正确，应为'年-月'。")
        print("用户时间范围中的日期部分格式不正确，应为'年-月'。")
        return False
    current_date = datetime.now()
    if start_date <= current_date <= end_date:

        print("【用户身份校验】用户在有效期内[激活]【√】")
        return True
    else:
        print("【用户身份校验】用户不在有效期内[跳过]【X】")
        return False    

def jiejiari():
    # 判断今天是否是节假日
    today = datetime.today().date()
    is_holiday = chinese_calendar.is_holiday(today)
    if is_holiday:
        return True
    else:
        return False


def yuexiu(mothxiu,sign_ins,jiaqi_ins):
    #根据当前月份的剩余天数、用户的签到天数、用户的假期天数以及月末的天数，来决定用户是否应该在今天工作。它使用一系列的逻辑判断和概率计算来达成决定。
    mothxiu = int(mothxiu)
    sign_ins = int(sign_ins)
    jiaqi_ins = int(jiaqi_ins)
    mothday = 31
    remaining_days = mothday - sign_ins
    gailv = 0
    # Calculate the probability of reaching the maximum days off
    max_days_off_probability = 0.6
    # Adjust the probability based on the remaining days and desired probability
    if remaining_days <= mothxiu:
        gailv = max_days_off_probability
    else:
        gailv = 0
    if jiaqi_ins >= mothxiu:
        return False
    if remaining_days > 25:
        gailv = 0.25
    elif remaining_days > 20:
        gailv = 0.30
    elif remaining_days > 15:
        gailv = 0.35
    elif remaining_days > 10:
        gailv = 0.40
    elif remaining_days > 5:
        gailv = 0.45
    gailv -= 0.05 * jiaqi_ins
    if jiaqi_ins == 3:
        gailv -= 0.13
    if random.random() <= gailv:
        return True
    else:
        return False

def encrypt(latitude, longitude):
    #纬度，经度
    # 要加密的经纬度数据
    # 设置公钥
    public_key_data = f'''-----BEGIN PUBLIC KEY-----
    {key_config}
    -----END PUBLIC KEY-----'''
    public_key = rsa.PublicKey.load_pkcs1_openssl_pem(public_key_data)
    # 分别加密经度和纬度
    encrypted_longitude = rsa.encrypt(str(longitude).encode(), public_key)
    encrypted_latitude = rsa.encrypt(str(latitude).encode(), public_key)
    # 将加密后的数据转换为base64编码
    encrypted_longitude_base64 = base64.b64encode(encrypted_longitude)
    encrypted_latitude_base64 = base64.b64encode(encrypted_latitude)
    return encrypted_longitude_base64.decode(),encrypted_latitude_base64.decode()

def extract_province_city(address):
    #返回 省名 市名
    pattern = re.compile(r'(\w+省|\w+市|\w+特别行政区)(\w*市)?')
    match = pattern.search(address)
    if match:
        province, city = match.groups()
        if '市' in province or '特别行政区' in province:
            return province, province
        if city is None:
            return province, None
        return province, city
    else:
        return None, None

def parse_time(time_str):
    # 将字符串 "HH:MM" 解析为小时和分钟
    time_parts = time_str.split(":")
    return int(time_parts[0]), int(time_parts[1])

async def qiandao(token,school_id,province,city,address,address_name,latitude,longitude,remark,time,name,account):
    target_hour, target_minute = parse_time(time)
    rnd = random.SystemRandom()
    while True:
        now = datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if now.hour > target_hour or (now.hour == target_hour and now.minute > target_minute):
            delta_sec = 0
            #logloglog_text = (f"{name} {account} {time} 已过签到时间，直接进行签到\n")
            print(f"{name} {account} {time} 已过签到时间，直接进行签到")
        else:
            delta_sec = (target_time - now).total_seconds()
        # 10% 的概率提前 1 到 5 分钟
        if rnd.random() < 0.1:
            early_sec = rnd.randint(1, 5) * 60
            # 如果 delta_sec 小于提前打印的时间，就不提前打印
            if delta_sec > early_sec:
                delta_sec -= early_sec
        try:
            await asyncio.sleep(delta_sec)
            latitude_bs4,longitude_bs4 = encrypt(latitude, longitude)
            qiandao = Xixunyun_qian(token,school_id,province,city,address,address_name,latitude_bs4,longitude_bs4,remark).get_qiandao()
            print(qiandao)
            if qiandao[0] == "error":
                if qiandao[1] == "请求超时，可能是网络问题":
                    #logloglog_text += f"{name} {account} 请求超时，可能是网络问题"
                    #logger.inf.info(#logloglog_text)
                    return "请求超时，可能是网络问题"
                elif qiandao[1] == "请求异常":
                    #logloglog_text += f"{name} {account}  请求异常" 
                    #logger.inf.info(#logloglog_text)
                    return "请求异常"
            if qiandao[0] == True:
                qiandao_days = qiandao[1]
                #logloglog_text += (f"{name} {account} 签到成功，连续签到 {qiandao_days}天")
                print(f"{name} {account} 签到成功，连续签到 {qiandao_days}天")
                #logger.inf.info(#logloglog_text)
                return True,(f"{name} {account} 成功"),qiandao_days
            elif qiandao[0] == False:
                qiandao_errow = qiandao[1]
                #logloglog_text += (f"{name} {account} 签到失败 问题：{qiandao_errow}")
                #logger.inf.info(#logloglog_text)
                return False,(f"{name} {account} 失败"),qiandao_errow
            await asyncio.sleep(0.1)
            break
        except Exception as e:
            #logloglog_text += (f"{name} {account} | 签到出问题了: {e}")
            #logger.inf.info(#logloglog_text)
            print(f"{name} {account} \n签到出问题了: {e}")
            return "ERROR",(f"{name} {account} 失败"),(f"签到出问题了: {e}")

async def main():
    qiandao_TF = []
    #logloglog_text = "启动任务分配库\n"
    # 获取用户列表
    users = user_data['users']
    users_len = len(users)
    bot_message = f"任务库执行报告\n数据库总用户：{users_len} 个\n"
    #logloglog_text += (f"数据库总用户：{users_len} 个\n")
    start_fenpei_time = time.time()
    #logger.inf.info(#logloglog_text)
    print(f"总用户：{users_len}")

    print("-----------------------------")
    # 遍历每个用户
    shushushu = 0
    for user in users:
        #logloglog_text = ""
        name = user['name']
        school_id = user['school_id']
        token = user['token']
        moth = user['moth']
        mothxiu = user['mothxiu']
        word_long = user['word_long']
        word_latit = user['word_latit']
        word_name = user['word_name']
        word_name_guishu = user['word_name_guishu']
        home_long = user['home_long']
        home_latit = user['home_latit']
        home_name = user['home_name']
        home_name_guishu = user['home_name_guishu']
        model = user['model']
        phone = user['phone']
        account = user['account']
        time_user = user['time']
        jiuxu = user['jiuxu']

        shushushu+=1
        #logloglog_text += (f"--------当前用户 {name} {phone} {account} -------------第{shushushu}个---——————-\n") 
        print(f"\n-------- 当前用户 姓名：{name} 手机号：{phone} 学号：{account}   -------------本次序列第【{shushushu}】位用户-------------\n") 
        if jiuxu == True:
            pass
        else:
            #logloglog_text += ("配置信息失效 跳过")
            print("配置信息失效 跳过")
        #判断是否存在于有效期中
        ageing_TF = ageing(moth)
        if ageing_TF is False:
            continue
        elif ageing_TF is True:
            #概率判断是否要休息
            user_record = Xixunyun_record(token,school_id).get_record()
            if len(user_record) > 3:
                user_record_errow = user_record
                if user_record_errow == "请求异常":
                    #logloglog_text += ("因为请求异常，用户Token更新失败")
                    print("因为请求异常，用户Token更新失败")
                    #logger.inf.info(#logloglog_text)
                    continue
                elif user_record_errow == "请求超时，可能是网络问题":
                    print("----------------出现请求超时情况，终止所有任务---------------------")
                    #logloglog_text += ("因为请求超时，可能是网络问题，终止所有任务")
                    #logger.inf.info(#logloglog_text)
                    break
                else:
                    #logloglog_text += ("错误[record]回复，用户[record]查询失败")
                    print("错误[record]回复，用户[record]查询失败",user_record_errow)
                    #logger.inf.info(#logloglog_text)
                    continue
            else:
                sign_ins,jiaqi_ins,abnormal_records_len = user_record
                print(f"——————————————————————\n本用户本月异常次数：{abnormal_records_len}\n——————————————————————\n")
                if jiejiari() is True:
                    #logloglog_text += ("今天是节假日,强制放假\n")
                    print("今天是节假日,强制放假")
                    address = home_name_guishu
                    address_name = home_name
                    province,city = extract_province_city(address)
                    latitude = home_latit
                    longitude = home_long
                    remark = "2"
                    #logloglog_text += (f"创建任务——姓名：{name},地址：{address},纬度：{latitude},经度：{longitude}，定时任务：{time_user},签到 【模式】 【放假】\n")
                    print(f"【创造计划任务】\n姓名：{name},地址：{address},纬度：{latitude},经度：{longitude},定时任务：{time_user},签到 模式 [放假]")
                    #logger.inf.info(#logloglog_text)
                    task = asyncio.create_task(qiandao(token,school_id,province,city,address,address_name,latitude,longitude,remark,time_user,name,account))
                    qiandao_TF.append(task)                        
                    continue
                elif jiejiari() is False:
                    #最大月休次数 本月已上班次数 本月休息次数
                    #logloglog_text += (f"最大月休数 {mothxiu},本月已上班打卡次数 {sign_ins},本月休息次数 {jiaqi_ins}")
                    print(f"【数据分析】\n【结论】最大月休数 {mothxiu},本月已上班打卡次数 {sign_ins},本月休息次数 {jiaqi_ins}")
                    #logloglog_text += ("判断是否需要继续------")
                    print("【?】判断是否需要上班.................")
                    user_yuexiu_FT = yuexiu(mothxiu,sign_ins,jiaqi_ins)
                    if user_yuexiu_FT is True:
                        #logloglog_text += ("今天休息")
                        print("【√】概率判断为[今天休息]")
                        address = home_name_guishu
                        address_name = home_name
                        province,city = extract_province_city(address)
                        latitude = home_latit
                        longitude = home_long
                        remark = "2"
                        #logloglog_text += (f"创建任务——姓名：{name},地址：{address},纬度：{latitude},经度：{longitude}，定时任务：{time_user}签到 【模式】 【放假】\n")
                        print(f"【创造计划任务】\n姓名：{name},地址：{address},纬度：{latitude},经度：{longitude},定时任务：{time_user},签到 模式 [放假]")
                        #logger.inf.info(#logloglog_text)
                        task = asyncio.create_task(qiandao(token,school_id,province,city,address,address_name,latitude,longitude,remark,time_user,name,account))
                        qiandao_TF.append(task)                        
                        continue
                        
                    elif user_yuexiu_FT is False:
                        #logloglog_text += ("今天上班")
                        print("【√】概率判断为[今天上班]")
                        #获取用户的地址
                        address = word_name_guishu
                        address_name = word_name
                        province,city = extract_province_city(address)
                        latitude = word_latit
                        longitude = word_long
                        remark = "0"
                        #logloglog_text += (f"创建任务——姓名：{name},地址：{address},纬度：{latitude},经度：{longitude}，定时任务：{time_user}签到","模式 上班\n")
                        print(f"【创造计划任务】\n姓名：{name},地址：{address},纬度：{latitude},经度：{longitude},定时任务：{time_user},签到 模式 [上班]")
                        #logger.inf.info(#logloglog_text)
                        task = asyncio.create_task(qiandao(token,school_id,province,city,address,address_name,latitude,longitude,remark,time_user,name,account))
                        qiandao_TF.append(task)                        
                        continue
    #logloglog_text = "所有用户任务已分配完毕，等待结果\n"
    #logger.inf.info(#logloglog_text)
    print("————————————————————————————————————————\n【任务库】所有用户任务已分配完毕，等待结果")
    end_fenpei_time = time.time()
    execution_fenpei_time = end_fenpei_time - start_fenpei_time
    print(f"【任务库】所有任务分配所花时间【{execution_fenpei_time:.2f}秒】")
    bot_message += (f"所有任务分配所花时间【{execution_fenpei_time:.2f}秒】\n")
    #logloglog_text += (f"所有任务分配所花时间【{execution_fenpei_time:.2f}秒】")
    start_task_back = time.time()
    results = await asyncio.gather(*qiandao_TF)
    #logloglog_text = "数据库——结果已返回\n"
    bot_message_sure = 0
    bot_message_error = 0
    for result in results:
        if isinstance(result, tuple):
            if result[0] == True:
                #logloglog_text += (f"{result[1]}\n")
                #logloglog_text += (f"已经连续签到 {result[2]} 天\n")
                bot_message += (f"{result[1]} 成功,连续签到【{result[2]}】天\n")
                bot_message_sure += 1
            elif result[0] == False:
                #logloglog_text += (f"{result[1]}\n")
                #logloglog_text += (f"{result[2]}\n")
                bot_message += (f"{result[1]} 失败,问题【{result[2]}】\n")
                bot_message_error += 1
            elif result[0] == "ERROR":
                #logloglog_text += (f"{result[1]}\n")
                #logloglog_text += (f"{result[2]}\n")
                bot_message += (f"{result[1]} 失败,问题【{result[2]}】\n")
                bot_message_error += 1
    #logloglog_text += "\n已获得所有结果，任务结束\n"
    end_task_back = time.time()
    execution_task_time = end_task_back - start_task_back
    print(f"\n【任务库】所有任务执行所花时间【{execution_task_time:.2f}秒】\n————————————————————————————————————————")
    #logloglog_text += (f"所有任务执行所花时间【{execution_task_time:.2f}秒】")
    bot_message += (f"所有任务执行所花时间【{execution_task_time:.2f}秒】")
    #logger.inf.info(#logloglog_text)
    print(f"最终结果：\n{results}\n")
    print("结束")
    #logloglog_text = (f"{bot_message}\n———————————\n任务库数据汇总\n用户总数：{users_len}个\n成功：{bot_message_sure}个\n失败:{bot_message_error}个\n")
    
    huizong_message = (f"{bot_message}\n————————————————————————————————————————\n任务库数据汇总\n用户总数：{users_len}个\n成功：{bot_message_sure}个\n失败:{bot_message_error}个")
    print(huizong_message)
    bot_message_tuisong = load_send()
    if bot_message_tuisong is not None:
        print("发现推送服务|正在推送")
        bot_message_tuisong("习讯云助手",huizong_message)
    
                       
if __name__ == "__main__":    
    with open(f'{weizhi}{os.sep}data{os.sep}user.json', 'r',encoding="utf-8") as f:
        user_data = json.load(f)

    asyncio.run(main())