# Test Paper: Adaptive Trust Calibration

## Abstract

This paper presents a novel approach to adaptive trust calibration in human-AI collaborative decision-making systems.

## 1. Introduction

Trust calibration is essential for effective human-AI collaboration. Previous work has shown that **overtrust** and **undertrust** can significantly impact system performance.

### 1.1 Research Questions

- How can we dynamically adjust interface strategies?
- What features indicate user trust state?

## 2. Method

Our approach uses a five-dimensional strategy space:

| Dimension | Levels | Description |
|-----------|--------|-------------|
| Automation (L) | 1-5 | Level of AI autonomy |
| Explanation (E) | 1-4 | Depth of explanations |
| Density (D) | 1-4 | Information density |

The trust estimation formula is:

$$BTI = \sum_{i=1}^{n} w_i \cdot f_i$$

where $w_i$ is the weight for feature $i$ and $f_i$ is the normalized feature value.

## 3. Experiments

We conducted experiments with 120 participants. Results show our method achieves 15% improvement in trust calibration accuracy.

## 4. Conclusion

We presented an adaptive trust calibration system that dynamically adjusts interface strategies based on user behavior.
