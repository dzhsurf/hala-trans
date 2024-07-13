const { override, addWebpackAlias } = require('customize-cra');
const path = require('path');

module.exports = override(
    addWebpackAlias({
        '@app': path.resolve(__dirname, 'src/app'),
        '@theme': path.resolve(__dirname, 'src/theme'),
        '@containers': path.resolve(__dirname, 'src/containers'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@services': path.resolve(__dirname, 'src/services'),
        '@features': path.resolve(__dirname, 'src/features'),
    })
);