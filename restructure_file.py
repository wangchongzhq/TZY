# -*- coding: utf-8 -*-

# Read the entire content of jieguo.txt
with open('jieguo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Identify the header section (lines 1-6)
header = lines[0:6]

# Identify the content section (line 7 onwards)
content = lines[7:]

# Create the new structure:
# 1. Content first
# 2. Add "说明,#genre#" line
# 3. Add the header at the end
new_content = content
new_content.append('说明,#genre#\n')
new_content.extend(header)

# Write the new structure back to jieguo.txt
with open('jieguo.txt', 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print("File structure updated successfully!")
