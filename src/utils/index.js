export const fetchData = async (url) => {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
};

export const parseNDVIData = (data) => {
    // Implement parsing logic for NDVI data
    return data.map(item => ({
        date: item.date,
        ndvi: item.ndvi,
    }));
};

export const calculatePhenology = (ndviData) => {
    // Implement calculations related to phenology
    const results = {};
    // Example calculation logic
    ndviData.forEach(item => {
        // Perform calculations
    });
    return results;
};