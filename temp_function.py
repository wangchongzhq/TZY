def is_hd_channel(channel_info):
    """判断是否为高清晰度频道"""
    name = channel_info.get('name', '').lower()
    tvg_name = channel_info.get('tvg_name', '').lower()
    group = channel_info.get('group', '').lower()
    
    # 检查是否包含高清关键字
    for keyword in HD_KEYWORDS:
        if (keyword.lower() in name or 
            keyword.lower() in tvg_name or 
            keyword.lower() in group):
            return True
    
    # 对于央视和卫视，默认认为是高清
    cctv_pattern = r'cctv'
    satellite_pattern = r'卫视'
    if (re.search(cctv_pattern, name) or 
        re.search(cctv_pattern, tvg_name) or
        re.search(satellite_pattern, name) or
        re.search(satellite_pattern, tvg_name)):
        return True
    
    return False