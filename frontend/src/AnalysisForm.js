import React, { useState } from 'react';
import axios from 'axios';

const AnalysisForm = () => {
    const [configPath, setConfigPath] = useState('');
    const [baseDir, setBaseDir] = useState('');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/analyze', {
                config_path: configPath,
                base_dir: baseDir,
            });
            setMessage(response.data.message);
        } catch (error) {
            setMessage('Error: ' + error.response.data.error);
        }
    };

    return (
        <div>
            <h1>Financial Analysis</h1>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Config Path:</label>
                    <input
                        type="text"
                        value={configPath}
                        onChange={(e) => setConfigPath(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Base Directory:</label>
                    <input
                        type="text"
                        value={baseDir}
                        onChange={(e) => setBaseDir(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Run Analysis</button>
            </form>
            {message && <p>{message}</p>}
        </div>
    );
};

export default AnalysisForm;
