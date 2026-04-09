import re

with open('/Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/hyred/src/App.tsx', 'r') as f:
    text = f.read()

# Replace root div
text = text.replace('className="min-h-screen bg-[var(--surface-lowest)] text-[var(--on-surface)] selection:bg-[var(--primary)] selection:text-[var(--surface-lowest)] relative overflow-x-hidden"', 'className="h-screen w-screen bg-[#1a1c1c] text-[#1a1c1c] relative overflow-hidden font-sans grid grid-cols-12 gap-[2px] p-[2px]"')

# Header
text = text.replace('className="sticky top-0 z-[60] bg-[var(--surface-container)] bg-opacity-95 backdrop-blur-3xl shadow-2xl"', 'className="col-span-12 sticky top-0 z-[60] bg-[#f9f9f9] border-b-[2px] border-[#1a1c1c] overflow-hidden"')

# Main wrapping
text = text.replace('className="max-w-[1600px] mx-auto p-8 relative"', 'className="col-span-12 relative flex flex-col h-full overflow-hidden bg-[#ffffff] p-8"')

# Remove fixed backgrounds
text = text.replace('bg-[var(--surface-lowest)]', 'bg-[#f9f9f9]').replace('bg-[var(--surface-container)]', 'bg-[#ffffff]').replace('bg-[var(--surface-highest)]', 'bg-[#f3f3f3]')
text = text.replace('text-[var(--on-surface)]', 'text-[#1a1c1c]').replace('text-[var(--on-surface-variant)]', 'text-[#a1a1aa]')

# Remove floating backgrounds
text = re.sub(r'shadow-\[.*?\]', '', text)
text = text.replace('rounded-full', '')
text = text.replace('rounded-md', '')
text = text.replace('rounded-lg', '')
text = text.replace('rounded-xl', '')
text = text.replace('rounded-sm', '')

with open('/Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/hyred/src/App.tsx', 'w') as f:
    f.write(text)

print("Hyred App.tsx updated.")
