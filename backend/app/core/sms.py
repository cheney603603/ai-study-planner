"""阿里云短信服务"""
import json
from typing import Optional
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("service.sms")

# 开发环境标志（无真实 API Key 时使用）
DEV_MODE = not settings.ALIYUN_SMS_ACCESS_KEY_ID or settings.ALIYUN_SMS_ACCESS_KEY_ID == "your-access-key-id"


class SMSService:
    """阿里云短信服务"""
    
    def __init__(self):
        self.sign_name = settings.ALIYUN_SMS_SIGN_NAME
        self.template_code = settings.ALIYUN_SMS_TEMPLATE_CODE
        self.access_key_id = settings.ALIYUN_SMS_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_SMS_ACCESS_KEY_SECRET
    
    async def send_verification_code(self, phone: str, code: str) -> bool:
        """
        发送验证码短信
        
        Args:
            phone: 手机号
            code: 验证码
        
        Returns:
            bool: 发送是否成功
        """
        logger.info(f"发送验证码: phone={phone}, code={code}")
        
        if DEV_MODE:
            logger.info(f"[开发模式] 模拟发送短信: {phone} -> 验证码 {code}")
            return True
        
        try:
            # TODO: 实现真实的阿里云短信发送
            # 参考: https://help.aliyun.com/document_detail/419284.html
            
            # 示例代码（待完善）
            # from aliyunsdkcore.client import AcsClient
            # from aliyunsdkcore.request import CommonRequest
            
            # client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')
            # request = CommonRequest()
            # request.set_accept_format('json')
            # request.set_domain('dysmsapi.aliyuncs.com')
            # request.set_method('POST')
            # request.set_protocol_type('https')
            # request.set_version('2017-05-25')
            # request.set_action_name('SendSms')
            # request.add_query_param('PhoneNumbers', phone)
            # request.add_query_param('SignName', self.sign_name)
            # request.add_query_param('TemplateCode', self.template_code)
            # request.add_query_param('TemplateParam', json.dumps({'code': code}))
            
            # response = client.do_action_with_exception(request)
            # return json.loads(response.decode())['Code'] == 'OK'
            
            logger.warning("生产环境短信发送未实现，请配置阿里云短信服务")
            return False
            
        except Exception as e:
            logger.error(f"短信发送失败: {str(e)}")
            return False


# 全局服务实例
sms_service = SMSService()
