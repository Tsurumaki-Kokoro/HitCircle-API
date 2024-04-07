import matplotlib.colors as mcolors
import numpy as np
import matplotlib as mpl

__input_values = np.array([0.1, 1.25, 2, 2.5, 3.3, 4.2, 4.9, 5.8, 6.7, 7.7, 9])
__normalized_values = (__input_values - np.min(__input_values)) / (np.max(__input_values) - np.min(__input_values))

# 定义对应的颜色
__colors = ['#4290FB', '#4FC0FF', '#4FFFD5', '#7CFF4F', '#F6F05C', '#FF8068', '#FF4E6F', '#C645B8', '#6563DE', '#18158E', '#000000']

# 创建颜色映射对象
__cmap = mcolors.LinearSegmentedColormap.from_list('difficultyColourSpectrum', list(zip(__normalized_values, __colors)), N=16384)
__norm = mpl.colors.Normalize(vmin=0, vmax=9)
ColorArr = mpl.cm.ScalarMappable(norm=__norm, cmap=__cmap).to_rgba(np.linspace(0, 9, 900), bytes=True)
