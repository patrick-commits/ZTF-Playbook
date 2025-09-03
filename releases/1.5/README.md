# v1.5

## What's New

### Framework Enhancements
- Introduced Site-deploy workflow for deploying Sites from Foundation Central
- Introduced Cluster-Create and Imaging-only Workflows which use Foundation Central

### PC operations
- Add Iam entities in PC using v4 APIs which include create Roles, UserGroups, Users, IAMKeys, AuthorizationPolicy, DirectoryServices
- Enable MarketPlace
- Enable Foundation Central
- Generate Foundation Central API keys

### Bug Fixes
- Fixed Bugs in Create VMs in PC
- Fixed a bug related to ipmi_netmask field in FoundationScript
- Fixed a bug in Create Object Stores

### PE operations
- As the v2 API Endpoint was deprecated for Virtual Switch, introduced v4 API endpoint for it as part of the CreateSubnetPe Script