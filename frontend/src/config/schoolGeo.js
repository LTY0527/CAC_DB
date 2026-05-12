export const SHANGHAI_GEOJSON_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/310000_full.json'

// 校区坐标基于公开主校区地址整理，仅用于公众端和政府端地图点位展示。
export const SCHOOL_GEO_POINTS = [
  {
    school_name: '上海交通大学',
    school_level: '双一流建设高校',
    campus_name: '闵行校区',
    address: '上海市闵行区东川路800号',
    lng: 121.4331,
    lat: 31.0252,
  },
  {
    school_name: '复旦大学',
    school_level: '双一流建设高校',
    campus_name: '邯郸校区',
    address: '上海市杨浦区邯郸路220号',
    lng: 121.5037,
    lat: 31.3358,
  },
  {
    school_name: '同济大学',
    school_level: '双一流建设高校',
    campus_name: '四平路校区',
    address: '上海市杨浦区四平路1239号',
    lng: 121.5062,
    lat: 31.2831,
  },
  {
    school_name: '华东师范大学',
    school_level: '双一流建设高校',
    campus_name: '中山北路校区',
    address: '上海市普陀区中山北路3663号',
    lng: 121.4019,
    lat: 31.2298,
  },
  {
    school_name: '华东理工大学',
    school_level: '双一流建设高校',
    campus_name: '徐汇校区',
    address: '上海市徐汇区梅陇路130号',
    lng: 121.4288,
    lat: 31.1419,
  },
  {
    school_name: '上海财经大学',
    school_level: '双一流建设高校',
    campus_name: '国定路校区',
    address: '上海市杨浦区国定路777号',
    lng: 121.5151,
    lat: 31.3054,
  },
  {
    school_name: '上海大学',
    school_level: '双一流建设高校',
    campus_name: '宝山校区',
    address: '上海市宝山区上大路99号',
    lng: 121.4586,
    lat: 31.3197,
  },
  {
    school_name: '东华大学',
    school_level: '双一流建设高校',
    campus_name: '延安路校区',
    address: '上海市长宁区延安西路1882号',
    lng: 121.4213,
    lat: 31.2107,
  },
  {
    school_name: '上海外国语大学',
    school_level: '双一流建设高校',
    campus_name: '虹口校区',
    address: '上海市虹口区大连西路550号',
    lng: 121.4854,
    lat: 31.2773,
  },
  {
    school_name: '上海理工大学',
    school_level: '应用理工特色高校',
    campus_name: '军工路校区',
    address: '上海市杨浦区军工路516号',
    lng: 121.5526,
    lat: 31.2917,
  },
]

export function getSchoolGeoPointMap() {
  return SCHOOL_GEO_POINTS.reduce((acc, item) => {
    acc[item.school_name] = item
    return acc
  }, {})
}
