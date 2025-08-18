import pytest
import numpy as np
from ca2roi.smoothing import (
    exponential_moving_average,
    smooth_intensity_trace,
    smooth_multiple_traces,
)


class TestExponentialMovingAverage:
    """Test cases for exponential moving average function."""

    def test_no_smoothing_alpha_zero(self):
        """Test that alpha=0 returns original data."""
        data = [1, 2, 3, 4, 5]
        result = exponential_moving_average(data, alpha=0)
        np.testing.assert_array_equal(result, np.array(data))

    def test_maximum_smoothing_alpha_one(self):
        """Test that alpha=1 gives maximum smoothing."""
        data = [1, 2, 3, 4, 5]
        result = exponential_moving_average(data, alpha=1)
        # With alpha=1, each point should be the current value
        expected = np.array([1, 2, 3, 4, 5])
        np.testing.assert_array_equal(result, expected)

    def test_medium_smoothing(self):
        """Test medium smoothing with alpha=0.5."""
        data = [1, 2, 3, 4, 5]
        result = exponential_moving_average(data, alpha=0.5)

        # Manual calculation for alpha=0.5:
        # s[0] = 1
        # s[1] = 0.5*2 + 0.5*1 = 1.5
        # s[2] = 0.5*3 + 0.5*1.5 = 2.25
        # s[3] = 0.5*4 + 0.5*2.25 = 3.125
        # s[4] = 0.5*5 + 0.5*3.125 = 4.0625
        expected = np.array([1, 1.5, 2.25, 3.125, 4.0625])
        np.testing.assert_array_almost_equal(result, expected, decimal=10)

    def test_debias_correction(self):
        """Test that debiasing correction works correctly."""
        data = [1, 2, 3, 4, 5]
        alpha = 0.3

        # Without debiasing
        result_no_debias = exponential_moving_average(data, alpha, debias=False)

        # With debiasing
        result_debias = exponential_moving_average(data, alpha, debias=True)

        # The debiased result should be different from non-debiased
        assert not np.array_equal(result_no_debias, result_debias)

        # The debiased result should be closer to the original data at the beginning
        # because it corrects for the initial bias
        assert abs(result_debias[0] - data[0]) < abs(result_no_debias[0] - data[0])

    def test_invalid_alpha_values(self):
        """Test that invalid alpha values raise ValueError."""
        data = [1, 2, 3, 4, 5]

        with pytest.raises(ValueError):
            exponential_moving_average(data, alpha=-0.1)

        with pytest.raises(ValueError):
            exponential_moving_average(data, alpha=1.1)

    def test_empty_data(self):
        """Test handling of empty data."""
        data = []
        result = exponential_moving_average(data, alpha=0.5)
        np.testing.assert_array_equal(result, np.array([]))

    def test_single_element(self):
        """Test handling of single element data."""
        data = [42]
        result = exponential_moving_average(data, alpha=0.5)
        np.testing.assert_array_equal(result, np.array([42]))

    def test_numpy_array_input(self):
        """Test that function works with numpy arrays."""
        data = np.array([1, 2, 3, 4, 5])
        result = exponential_moving_average(data, alpha=0.5)
        assert isinstance(result, np.ndarray)
        assert len(result) == len(data)

    def test_multidimensional_array_error(self):
        """Test that multidimensional arrays raise ValueError."""
        data = np.array([[1, 2], [3, 4]])

        with pytest.raises(ValueError):
            exponential_moving_average(data, alpha=0.5)


class TestSmoothIntensityTrace:
    """Test cases for smooth_intensity_trace function."""

    def test_no_smoothing_zero_factor(self):
        """Test that smoothing factor 0 returns original data."""
        data = [1, 2, 3, 4, 5]
        result = smooth_intensity_trace(data, smoothing_factor=0)
        np.testing.assert_array_equal(result, np.array(data))

    def test_with_smoothing(self):
        """Test that smoothing is applied when factor > 0."""
        data = [1, 2, 3, 4, 5]
        result = smooth_intensity_trace(data, smoothing_factor=0.5)

        # Should be different from original due to smoothing
        assert not np.array_equal(result, np.array(data))

        # Should have same length
        assert len(result) == len(data)

    def test_numpy_array_input(self):
        """Test that function works with numpy arrays."""
        data = np.array([1, 2, 3, 4, 5])
        result = smooth_intensity_trace(data, smoothing_factor=0.3)
        assert isinstance(result, np.ndarray)
        assert len(result) == len(data)


class TestSmoothMultipleTraces:
    """Test cases for smooth_multiple_traces function."""

    def test_no_smoothing_zero_factor(self):
        """Test that smoothing factor 0 returns original data."""
        traces = [[1, 2, 3], [4, 5, 6]]
        result = smooth_multiple_traces(traces, smoothing_factor=0)

        assert len(result) == len(traces)
        for i, trace in enumerate(traces):
            np.testing.assert_array_equal(result[i], np.array(trace))

    def test_with_smoothing(self):
        """Test that smoothing is applied to all traces."""
        traces = [[1, 2, 3], [4, 5, 6]]
        result = smooth_multiple_traces(traces, smoothing_factor=0.5)

        assert len(result) == len(traces)
        for i, original_trace in enumerate(traces):
            # Each trace should be smoothed (different from original)
            assert not np.array_equal(result[i], np.array(original_trace))
            # Should have same length
            assert len(result[i]) == len(original_trace)

    def test_empty_traces_list(self):
        """Test handling of empty traces list."""
        traces = []
        result = smooth_multiple_traces(traces, smoothing_factor=0.5)
        assert result == []

    def test_mixed_input_types(self):
        """Test that function works with mixed list/numpy array inputs."""
        traces = [[1, 2, 3], np.array([4, 5, 6])]
        result = smooth_multiple_traces(traces, smoothing_factor=0.3)

        assert len(result) == len(traces)
        for trace in result:
            assert isinstance(trace, np.ndarray)


if __name__ == "__main__":
    pytest.main([__file__])
