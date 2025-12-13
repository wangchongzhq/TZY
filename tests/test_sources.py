import unified_sources

print('UNIFIED_SOURCES loaded successfully')
print(f'Total sources: {len(unified_sources.UNIFIED_SOURCES)}')
print('First 5 sources:')
for source in unified_sources.UNIFIED_SOURCES[:5]:
    print(f'  - {source}')
print('Last 5 sources:')
for source in unified_sources.UNIFIED_SOURCES[-5:]:
    print(f'  - {source}')
