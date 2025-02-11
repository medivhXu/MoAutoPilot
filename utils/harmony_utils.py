class HarmonyUtils:
    """鸿蒙系统特定工具类"""
    
    @staticmethod
    def get_device_info(driver):
        """获取鸿蒙设备信息"""
        try:
            return {
                'deviceType': driver.execute_script('harmony: getDeviceType'),
                'systemVersion': driver.execute_script('harmony: getSystemVersion'),
                'deviceModel': driver.execute_script('harmony: getDeviceModel')
            }
        except Exception as e:
            print(f"获取设备信息失败: {str(e)}")
            return None
    
    @staticmethod
    def handle_permissions(driver):
        """处理鸿蒙权限弹窗"""
        try:
            allow_btn = driver.find_element_by_text("允许")
            if allow_btn:
                allow_btn.click()
        except:
            pass